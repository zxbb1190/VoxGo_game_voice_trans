param([int]$Port = 17853, [Parameter(Mandatory=$true)][string]$Evidence, [Parameter(Mandatory=$true)][string]$StopFile)
$ErrorActionPreference = 'Stop'
# Test harness only. This server has no upstream connection or forwarding code.
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
public static class VoxGoLocalAcceptance {
  static readonly object Gate = new object();
  static string Log;
  static int Blocked, Mock;
  static void Record(string kind, int status, int bytes) {
    lock(Gate) File.AppendAllText(Log, "{\"utc\":\""+DateTime.UtcNow.ToString("o")+"\",\"kind\":\""+kind+"\",\"status\":"+status+",\"body_bytes\":"+bytes+"}\n",new UTF8Encoding(false));
  }
  static void Reply(NetworkStream stream,int status,string json) {
    byte[] data=Encoding.UTF8.GetBytes(json);
    byte[] header=Encoding.ASCII.GetBytes("HTTP/1.1 "+status+" Test\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: "+data.Length+"\r\nConnection: close\r\n\r\n");
    stream.Write(header,0,header.Length);stream.Write(data,0,data.Length);
  }
  static void Handle(object value) {
    using(TcpClient client=(TcpClient)value) {
      client.ReceiveTimeout=5000;client.SendTimeout=5000;
      try { using(NetworkStream stream=client.GetStream()) {
        MemoryStream header=new MemoryStream();int b,last=0;
        while(header.Length<32768 && (b=stream.ReadByte())>=0) {
          header.WriteByte((byte)b);last=((last<<8)|b);
          if(last==0x0d0a0d0a) break;
        }
        string[] lines=Encoding.ASCII.GetString(header.ToArray()).Split(new string[]{"\r\n"},StringSplitOptions.None);
        string[] first=lines[0].Split(' ');
        if(first.Length<2) return;
        string method=first[0],path=first[1].Split('?')[0];int length=0;
        foreach(string line in lines) if(line.StartsWith("Content-Length:",StringComparison.OrdinalIgnoreCase)) Int32.TryParse(line.Substring(15).Trim(),out length);
        if(length<0 || length>262144) { Reply(stream,413,"{}");return; }
        if(method=="CONNECT" || path.StartsWith("http:") || path.StartsWith("https:")) {
          Interlocked.Increment(ref Blocked);Record("external_request_blocked",502,0);
          Reply(stream,502,"{\"error\":\"Acceptance proxy: external traffic is blocked; no upstream connection\"}");return;
        }
        byte[] body=new byte[length];int read=0,count;
        while(read<length && (count=stream.Read(body,read,length-read))>0) read+=count;
        if(method=="GET" && path=="/_acceptance/health") {
          Reply(stream,200,"{\"scope\":\"VoxGo-caed9130-local-only\",\"external_forwarded\":0,\"blocked\":"+Blocked+",\"mock_requests\":"+Mock+"}");return;
        }
        if(method=="POST" && path.EndsWith("/chat/completions")) {
          Interlocked.Increment(ref Mock);
          if(path.StartsWith("/429/")) {Record("local_mock_rate_limit",429,read);Reply(stream,429,"{\"error\":{\"message\":\"LOCAL TEST ONLY: simulated rate limit\"}}");return;}
          string text=path.StartsWith("/empty/") ? "" : "【本地模拟，非真实翻译】字幕链路已收到识别文本。";
          Record(text==""?"local_mock_empty":"local_mock_subtitle",200,read);
          Reply(stream,200,"{\"choices\":[{\"message\":{\"content\":\""+text+"\"},\"finish_reason\":\"stop\"}],\"model\":\"LOCAL_ACCEPTANCE_STUB\"}");return;
        }
        Record("local_route_rejected",404,read);Reply(stream,404,"{}");
      }} catch { Record("local_connection_closed",0,0); }
    }
  }
  public static void Run(int port,string log,string stop) {
    Log=log;TcpListener listener=new TcpListener(IPAddress.Loopback,port);listener.Start();
    try { while(!File.Exists(stop)) {
      if(listener.Pending()) ThreadPool.QueueUserWorkItem(Handle,listener.AcceptTcpClient());
      else Thread.Sleep(25);
    }} finally { listener.Stop(); }
  }
}
'@
[VoxGoLocalAcceptance]::Run($Port,(Join-Path $Evidence 'local-only-server.jsonl'),$StopFile)
