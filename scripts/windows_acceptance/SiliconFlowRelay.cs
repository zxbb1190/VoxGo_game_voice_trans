// Acceptance tooling only; never compiled into the shipped VoxGo client.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;

namespace VoxGoAcceptance {
    public sealed class UpstreamReply {
        public int Status;
        public byte[] Body;
        public UpstreamReply(int status, byte[] body) { Status = status; Body = body; }
    }

    // The CLI always constructs SiliconFlowUpstream. Tests inject an in-memory
    // implementation, so no test endpoint or credential can enable live calls.
    public interface ITranslationUpstream { UpstreamReply Send(byte[] body); }

    public sealed class SiliconFlowUpstream : ITranslationUpstream {
        public const string Endpoint = "https://api.siliconflow.cn/v1/chat/completions";
        private readonly string key;
        public SiliconFlowUpstream(string apiKey) {
            if (String.IsNullOrWhiteSpace(apiKey) || apiKey.IndexOfAny(new char[] {'\r', '\n'}) >= 0)
                throw new ArgumentException("Existing SiliconFlow credential unavailable");
            key = apiKey.Trim();
        }
        public UpstreamReply Send(byte[] body) {
            var request = (HttpWebRequest)WebRequest.Create(Endpoint);
            request.Method = "POST";
            request.Proxy = null;
            request.AllowAutoRedirect = false;
            request.KeepAlive = false;
            request.Timeout = 12000;
            request.ReadWriteTimeout = 12000;
            request.ServicePoint.Expect100Continue = false;
            request.ContentType = "application/json; charset=utf-8";
            request.Headers["Authorization"] = "Bearer " + key;
            request.ContentLength = body.Length;
            try {
                using (var stream = request.GetRequestStream()) stream.Write(body, 0, body.Length);
                HttpWebResponse response;
                try { response = (HttpWebResponse)request.GetResponse(); }
                catch (WebException error) {
                    response = error.Response as HttpWebResponse;
                    if (response == null) {
                        return Error(error.Status == WebExceptionStatus.Timeout ? 504 : 502,
                                     error.Status == WebExceptionStatus.Timeout ? "upstream_timeout" : "upstream_network_error");
                    }
                }
                using (response) {
                    int status = (int)response.StatusCode;
                    if (status >= 300 && status < 400) return Error(502, "upstream_redirect_blocked");
                    using (var stream = response.GetResponseStream())
                    using (var result = new MemoryStream()) {
                        var buffer = new byte[8192]; int read;
                        while ((read = stream.Read(buffer, 0, buffer.Length)) > 0) {
                            if (result.Length + read > 1048576) return Error(502, "upstream_response_too_large");
                            result.Write(buffer, 0, read);
                        }
                        // Do not let provider errors echo the real credential into app.log.
                        var text = Encoding.UTF8.GetString(result.ToArray()).Replace(key, "[REDACTED]");
                        return new UpstreamReply(status, Encoding.UTF8.GetBytes(text));
                    }
                }
            } catch { return Error(502, "upstream_connection_failed"); }
            finally { request.Abort(); }
        }
        static UpstreamReply Error(int status, string code) {
            return new UpstreamReply(status, Encoding.UTF8.GetBytes("{\"error\":{\"message\":\"" + code + "\"}}"));
        }
    }

    public sealed class OnlineRelay {
        public const string Scope = "VoxGo-caed9130-online-hunyuan-only";
        public const string Model = "tencent/Hunyuan-MT-7B";
        private readonly int port;
        private readonly string token, instance, logPath;
        private readonly ITranslationUpstream upstream;
        private readonly object logGate = new object();
        private readonly SemaphoreSlim inFlight = new SemaphoreSlim(1, 1);
        private int attempts, blocked, completed;
        private volatile bool journalFailed;

        public OnlineRelay(int listenPort, string localToken, string instanceId, string evidence,
                           ITranslationUpstream translationUpstream) {
            if (listenPort < 1 || listenPort > 65535 || String.IsNullOrEmpty(localToken) || localToken.Length < 32)
                throw new ArgumentException("Invalid local relay configuration");
            port = listenPort; token = localToken; instance = instanceId; upstream = translationUpstream;
            Directory.CreateDirectory(evidence);
            logPath = Path.Combine(evidence, "online-relay.jsonl");
        }

        static JavaScriptSerializer Json() {
            return new JavaScriptSerializer { MaxJsonLength = 1048576, RecursionLimit = 24 };
        }
        private void Record(string kind, int status, int bytes, int attempt, long elapsed,
                            IDictionary<string, object> usage) {
            var row = new Dictionary<string, object> {
                {"utc", DateTime.UtcNow.ToString("o")}, {"instance", instance}, {"kind", kind},
                {"status", status}, {"request_bytes", bytes}, {"attempt", attempt},
                {"upstream_ms", elapsed}, {"model", Model}
            };
            // Only fixed numeric usage keys; never persist prompts, audio, headers,
            // provider error bodies or the real/local credentials.
            if (usage != null) {
                foreach (var name in new string[] {"prompt_tokens", "completion_tokens", "total_tokens"}) {
                    object value;
                    if (usage.TryGetValue(name, out value) && (value is int || value is long || value is decimal))
                        row[name] = value;
                }
            }
            lock (logGate) {
                try { File.AppendAllText(logPath, Json().Serialize(row) + "\n", new UTF8Encoding(false)); }
                catch { journalFailed = true; throw; }
            }
        }
        private static void Reply(NetworkStream stream, int status, byte[] body) {
            byte[] header = Encoding.ASCII.GetBytes("HTTP/1.1 " + status + " Acceptance\r\n" +
                "Content-Type: application/json; charset=utf-8\r\nContent-Length: " + body.Length +
                "\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n");
            stream.Write(header, 0, header.Length); stream.Write(body, 0, body.Length);
        }
        private static void Error(NetworkStream stream, int status, string code) {
            Reply(stream, status, Encoding.UTF8.GetBytes("{\"error\":{\"message\":\"" + code + "\"}}"));
        }
        private void Block(NetworkStream stream, int status, string code) {
            Interlocked.Increment(ref blocked);
            Record(code, status, 0, 0, 0, null);
            Error(stream, status, code);
        }
        private static bool Same(string left, string right) {
            if (left == null || right == null) return false;
            int difference = left.Length ^ right.Length;
            for (int i = 0; i < Math.Min(left.Length, right.Length); i++) difference |= left[i] ^ right[i];
            return difference == 0;
        }
        private static bool ValidPayload(byte[] body) {
            try {
                var value = Json().DeserializeObject(new UTF8Encoding(false, true).GetString(body)) as Dictionary<string, object>;
                if (value == null || value.Count != 5) return false;
                foreach (var key in new string[] {"model", "messages", "max_tokens", "temperature", "stream"})
                    if (!value.ContainsKey(key)) return false;
                if (!Object.Equals(value["model"], Model) || !Object.Equals(value["stream"], false)) return false;
                if (!(value["max_tokens"] is int) || (int)value["max_tokens"] < 1 || (int)value["max_tokens"] > 4096)
                    return false;
                object temperature = value["temperature"];
                if (!(temperature is int || temperature is decimal || temperature is double)) return false;
                double number = Convert.ToDouble(temperature);
                if (Double.IsNaN(number) || Double.IsInfinity(number) || number < 0 || number > 2) return false;
                var messages = value["messages"] as object[];
                if (messages == null || messages.Length < 2 || messages.Length > 32) return false;
                foreach (object entry in messages) {
                    var message = entry as Dictionary<string, object>;
                    if (message == null || message.Count != 2 || !message.ContainsKey("role") || !message.ContainsKey("content"))
                        return false;
                    string role = message["role"] as string, content = message["content"] as string;
                    if ((role != "system" && role != "user" && role != "assistant") || String.IsNullOrWhiteSpace(content))
                        return false;
                }
                return true;
            } catch { return false; }
        }

        private void Handle(object value) {
            using (var client = (TcpClient)value) {
                client.ReceiveTimeout = 5000; client.SendTimeout = 5000;
                try { using (NetworkStream stream = client.GetStream()) {
                    var header = new MemoryStream(); int b, tail = 0; bool finished = false;
                    while (header.Length < 16384 && (b = stream.ReadByte()) >= 0) {
                        header.WriteByte((byte)b); tail = (tail << 8) | b;
                        if (tail == 0x0d0a0d0a) { finished = true; break; }
                    }
                    if (!finished) { Block(stream, 400, "invalid_header"); return; }
                    string[] lines = Encoding.ASCII.GetString(header.ToArray()).Split(new string[] {"\r\n"}, StringSplitOptions.None);
                    string[] first = lines[0].Split(' ');
                    if (first.Length != 3 || (first[2] != "HTTP/1.1" && first[2] != "HTTP/1.0")) { Block(stream, 400, "invalid_request_line"); return; }
                    string method = first[0], path = first[1];
                    // No HTTP proxying, CONNECT tunnels, redirects or general URL relay.
                    // Reject these BEFORE reading any telemetry/body bytes.
                    if (method == "CONNECT" || path.StartsWith("http:", StringComparison.OrdinalIgnoreCase) ||
                        path.StartsWith("https:", StringComparison.OrdinalIgnoreCase)) {
                        Block(stream, 502, "external_request_blocked"); return;
                    }
                    var headers = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
                    for (int i = 1; i < lines.Length; i++) {
                        if (lines[i].Length == 0) break;
                        int colon = lines[i].IndexOf(':');
                        if (colon <= 0 || Char.IsWhiteSpace(lines[i][0])) { Block(stream, 400, "invalid_header"); return; }
                        string name = lines[i].Substring(0, colon), content = lines[i].Substring(colon + 1).Trim();
                        if (headers.ContainsKey(name)) { Block(stream, 400, "duplicate_header"); return; }
                        headers.Add(name, content);
                    }
                    string host;
                    if (!headers.TryGetValue("Host", out host) || host != "127.0.0.1:" + port ||
                        headers.ContainsKey("Origin") || headers.ContainsKey("Transfer-Encoding")) {
                        Block(stream, 403, "invalid_local_origin"); return;
                    }
                    if (method == "GET" && path == "/_acceptance/health") {
                        var health = new Dictionary<string, object> {
                            {"scope", Scope}, {"instance", instance}, {"model", Model},
                            {"upstream_attempts", attempts}, {"completed", completed}, {"blocked", blocked},
                            {"journal_failed", journalFailed}, {"full", "denied_required"},
                            {"automatic_retries", false}, {"budget_limit", null}
                        };
                        Reply(stream, 200, Encoding.UTF8.GetBytes(Json().Serialize(health))); return;
                    }
                    if (method != "POST" || path != "/v1/chat/completions") {
                        Block(stream, 403, "route_blocked"); return;
                    }
                    string authorization;
                    if (!headers.TryGetValue("Authorization", out authorization) || !Same(authorization, "Bearer " + token)) {
                        Block(stream, 401, "local_session_required"); return;
                    }
                    string lengthText, type; int length;
                    if (!headers.TryGetValue("Content-Length", out lengthText) || !Int32.TryParse(lengthText, out length) ||
                        length <= 0 || length > 65536 || !headers.TryGetValue("Content-Type", out type) ||
                        !type.StartsWith("application/json", StringComparison.OrdinalIgnoreCase)) {
                        Block(stream, 400, "invalid_body_headers"); return;
                    }
                    var body = new byte[length]; int offset = 0, read;
                    while (offset < length && (read = stream.Read(body, offset, length - offset)) > 0) offset += read;
                    if (offset != length || !ValidPayload(body)) { Block(stream, 400, "invalid_translation_payload"); return; }
                    if (journalFailed) { Error(stream, 503, "journal_unavailable"); return; }
                    if (!inFlight.Wait(0)) { Error(stream, 429, "local_relay_busy_no_retry"); return; }
                    try {
                        // Durable reservation occurs before the one and only upstream Send.
                        int attempt = Interlocked.Increment(ref attempts);
                        Record("attempt_reserved", 0, length, attempt, 0, null);
                        var timer = Stopwatch.StartNew();
                        UpstreamReply response;
                        try { response = upstream.Send(body); }
                        catch { response = new UpstreamReply(502, Encoding.UTF8.GetBytes("{\"error\":{\"message\":\"upstream_failed\"}}")); }
                        timer.Stop();
                        IDictionary<string, object> usage = null;
                        try {
                            var result = Json().DeserializeObject(Encoding.UTF8.GetString(response.Body)) as Dictionary<string, object>;
                            object data;
                            if (result != null && result.TryGetValue("usage", out data)) usage = data as Dictionary<string, object>;
                        } catch { }
                        Record("attempt_completed", response.Status, length, attempt, timer.ElapsedMilliseconds, usage);
                        Interlocked.Increment(ref completed);
                        Reply(stream, response.Status, response.Body);
                    } finally { inFlight.Release(); }
                }} catch {
                    // Never print request text, credentials or exception/provider bodies.
                    // A failed reservation fails closed, before the upstream operation.
                }
            }
        }

        public void Run(string stopFile) {
            var listener = new TcpListener(IPAddress.Loopback, port);
            listener.ExclusiveAddressUse = true;
            listener.Start();
            try {
                while (!File.Exists(stopFile)) {
                    if (listener.Pending()) ThreadPool.QueueUserWorkItem(Handle, listener.AcceptTcpClient());
                    else Thread.Sleep(25);
                }
            } finally { listener.Stop(); }
        }
    }
}
