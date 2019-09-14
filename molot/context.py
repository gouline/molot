import os
import shutil
import logging
import urllib.request
import subprocess

class Context:
    """Base context with common operations.
    """

    def ensure_dir(self, path: str, keep_files: bool):
        """Ensures directory path exists.
        
        Arguments:
            path {str} -- Directory path.
            keep_files {bool} -- Keep existing files if already exists if true.
        """

        if os.path.exists(path):
            if not keep_files:
                shutil.rmtree(path)
                os.makedirs(path)
        else:
            os.makedirs(path)

    def download_files(self, file_urls: dict, out_path: str, ignore_existing: bool = False):
        """Downloads files into target directory.
        
        Arguments:
            file_urls {dict} -- Dict of filename => url for download.
            out_path {str} -- Output directory path.
        
        Keyword Arguments:
            ignore_existing {bool} -- Ignores existing files and re-downloads if true. (default: {False})
        """

        if not ignore_existing:
            existing_files = os.listdir(out_path)
            for f in existing_files:
                if f in file_urls:
                    logging.info("Already exists %s", f)
                    file_urls.pop(f, None)
                else:
                    os.remove(os.path.join(out_path, f))

        for filename in file_urls:
            url = file_urls[filename]

            logging.info("Downloading %s", url)
            urllib.request.urlretrieve(url, os.path.join(out_path, filename))
    
    def add_git_hash(self, out_path: str):
        """Adds Git hash to output.
        
        Arguments:
            out_path {str} -- Output directory path.
        """

        process = subprocess.Popen(['git', 'rev-parse', '--verify', 'HEAD'], stdout=subprocess.PIPE)
        output = process.communicate()[0] \
            .decode('utf-8') \
            .replace('\n', '')

        logging.info("Writing Git hash %s", output)
        out_file_path = os.path.join(out_path, 'git-hash')
        with open(out_file_path, 'w') as file:
            file.write(output)
