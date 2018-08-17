import subprocess
import json
import os

from .submodule_base import SubmoduleBaseclass


class ManalyzeSubmodule(SubmoduleBaseclass):
    """Manalyze submodule implements the static analysis tool by @JusticeRage
    (https://github.com/JusticeRage/Manalyze)"""

    def __init__(self, **kwargs):
        SubmoduleBaseclass.__init__(self)

        self.use_docker = kwargs.get('use_docker', False)
        self.use_binary = kwargs.get('use_binary', False)
        self.binary_path = kwargs.get('binary_path', None)

        self.name = 'Manalyze'

    def check_file(self, **kwargs):
        """
        Manalyze is for PE files.
        """
        try:
            if kwargs.get('filetype') in ['Win32 EXE', 'Win64 EXE']:
                return True
        except KeyError:
            return False
        return False

    def run_local_manalyze(self, filepath):
        sp = subprocess.run([
            self.binary_path,
            '--dump=imports,exports,sections',
            '--hashes',
            '--pe={}'.format(filepath),
            '--plugins=clamav,compilers,peid,strings,findcrypt,btcaddress,packer,imports,resources,mitigation,authenticode',
            '--output=json'
        ], stdout=subprocess.PIPE, cwd=os.path.split(self.binary_path)[0])
        result = sp.stdout
        result = json.loads(result.decode('utf-8'))
        return result[filepath]

    def run_docker_manalyze(self, filepath):
        filepath, filename = os.path.split(filepath)
        sp = subprocess.run([
            'docker',
            'run',
            '--rm',
            '-v',
            '{}:/data'.format(filepath),
            'evanowe/manalyze',
            '/Manalyze/bin/manalyze',
            '--dump=imports,exports,sections',
            '--hashes',
            '--pe=/data/{}'.format(filename),
            '--plugins=clamav,compilers,peid,strings,findcrypt,btcaddress,packer,imports,resources,mitigation,authenticode',
            '--output=json'
        ], stdout=subprocess.PIPE)
        result = sp.stdout
        result = json.loads(result.decode('utf-8'))
        return result[result.keys()[0]]

    def build_results(self, results):
        """Properly format the results"""
        self.add_result_subsection(
            'Exploit mitigation techniques',
            {
                'level': results.get('Plugins', {}).get('mitigation', {}).get('level', None),
                'summary': results.get('Plugins', {}).get('mitigation', {}).get('summary', None),
                'content': results.get('Plugins', {}).get('mitigation', {}).get('plugin_output', None)
            }
        )
        self.add_result_subsection(
            'Suspicious strings',
            {
                'level': results.get('Plugins', {}).get('strings', {}).get('level', None),
                'summary': results.get('Plugins', {}).get('strings', {}).get('summary', None),
                'content': results.get('Plugins', {}).get('strings', {}).get('plugin_output', None)
            }
        )
        self.add_result_subsection(
            'Suspicious imports',
            {
                'level': results.get('Plugins', {}).get('imports', {}).get('level', None),
                'summary': results.get('Plugins', {}).get('imports', {}).get('summary', None),
                'content': results.get('Plugins', {}).get('imports', {}).get('plugin_output', None)
            }
        )
        self.add_result_subsection('Manalyze raw output', json.dumps(results, indent=4))

    def analyze_file(self, path):
        results = {}
        if self.use_docker:
            results = self.run_docker_manalyze(path)
        elif self.use_binary and self.binary_path and self.binary_path != '':
            results = self.run_local_manalyze(path)
        self.build_results(results)
        return self.results
