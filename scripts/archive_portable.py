"""Stream release ZIPs without buffering large model/CUDA files in memory."""
import argparse
import os
from pathlib import Path
import stat
import tempfile
import zipfile


def archive_directory(source, destination):
    source = Path(source).absolute()
    destination = Path(destination).absolute()

    def reject_link(path):
        metadata = path.lstat()
        if path.is_symlink() or getattr(metadata, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError('Release archive source contains a link or reparse point')

    reject_link(source)
    source = source.resolve(strict=True)
    if not source.is_dir():
        raise ValueError('Release archive source must be a directory')
    if destination.resolve().is_relative_to(source):
        raise ValueError('Archive destination must be outside the source tree')
    if destination.exists():
        raise FileExistsError(destination)
    entries = sorted(source.rglob('*'))
    for path in entries:
        reject_link(path)
        if not path.is_dir() and not path.is_file():
            raise ValueError('Unsupported release archive input')
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=destination.name + '.', suffix='.partial', dir=destination.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6, allowZip64=True) as archive:
            archive.write(source, source.name + '/')
            for path in entries:
                # ZipFile.write streams file content; never read a whole model/DLL.
                archive.write(path, source.name + '/' + path.relative_to(source).as_posix())
        if destination.exists():
            raise FileExistsError(destination)
        temporary.rename(destination)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    arguments = parser.parse_args()
    archive_directory(arguments.source, arguments.destination)
