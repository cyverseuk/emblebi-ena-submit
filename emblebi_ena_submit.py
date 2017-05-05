#! /usr/bin/env python

__author__ = 'Paul Sarando, Rob Davey (EI)'

import config.emblebi_ena_submit_properties

from metadata_client import MetadataClient
from genshi.template import TemplateLoader
from lxml import etree
from argparse import ArgumentParser
from subprocess import call

import os
import shutil

class EnaDataFileUploader:
    def __init__(self, ascp_cmd, ena_user, ena_host, ena_sumbit_path):
        self.ascp_cmd = ascp_cmd
        self.upload_dest = '{0}@{1}:{2}'.format(ena_user, ena_host, ena_sumbit_path)

    def upload_datafiles(self, submit_dir, input_paths):
        # Collect the submission files from the input paths into the submission dir
        src_files = {}
        for path in input_paths:
            filename = os.path.basename(path)
            if filename in src_files:
                raise Exception("Duplicate filenames found in input directory:\n{0}\n{1}".format(src_files[filename], path))
            src_files[filename] = path

            shutil.move(path, os.path.join(submit_dir, filename))

        ascp_cmd = self.ascp_cmd + [
            "-i", self.private_key_path,
            submit_dir,
            self.upload_dest
        ]

        try:
            retcode = call(ascp_cmd)
            if retcode != 0:
                raise Exception("Upload error: {0}".format(-retcode))

            # The file uploads were successful, so upload a 'submit.ready' file to complete the submission.
            submit_ready = "submit.ready"
            open(os.path.join(submit_dir, submit_ready), 'a').close()

            # Calling the same upload command with the same submit directory will skip all files already
            # successfully uploaded, and only upload the new 'submit.ready' file.
            retcode = call(ascp_cmd)
            if retcode != 0:
                raise Exception("Error uploading '{0}' file: {1}".format(submit_ready, -retcode))
        except OSError as e:
            raise Exception("Aspera Connect upload failed", e)

        # Clean up: Move input files back into their original directories,
        # so they are not transferred as outputs, but can be preserved as inputs
        for filename in src_files:
            shutil.move(os.path.join(submit_dir, filename), src_files[filename])

usage = 'emblebi_ena_submit.py [options]'

desc = """
Prepares files from the Discovery Environment Data Store for submission to
the EMBL EBI European Nucleotide Archive (ENA), alongside provided XML documents.
"""

# Parse the command-line options.
parser = ArgumentParser(usage = usage, description = desc, add_help = False)
parser.add_argument('-s', '--submit-mode', dest = 'submit_mode',
                    default = 'ADD',
                    help = 'specify if the ENA submission is an ENA "ADD" (default) or an "UPDATE" request.')
#parser.add_argument('-i', '--private-key', dest = 'private_key_path',
#                    default = config.emblebi_ena_submit_properties.private_key_path,
#                    help = '(optional) specify an alternative path to the id_rsa private-key file.')
#parser.add_argument('-i', '--password', dest = 'password',
#                    required = True,
#                    help = 'password for the ascp command')
parser.add_argument('-f', '--input-dir', dest = 'input_dir',
                    help = 'specify the path to the input folder to submit to ENA')
parser.add_argument('-id', '--submission-id', dest = 'submission_id',
                    required = True,
                    help = 'specify a unique submission ID to use as a folder name.')
parser.add_argument('-p', '--project-accession', dest = 'project_accession',
                    help = 'a project accession is required for updating existing records')
parser.add_argument('-sub', '--submission-xml', dest = 'submission_xml',
                    required = True,
                    help = 'specify the path to the ENA Submission metadata file.')
parser.add_argument('-pro', '--project-xml', dest = 'project_xml',
                    required = True,
                    help = 'specify the path to the ENA Project metadata file.')
parser.add_argument('-sam', '--sample-xml', dest = 'sample_xml',
                    required = True,
                    help = 'specify the path to the ENA Sample metadata file.')
parser.add_argument('-exp', '--experiment-xml', dest = 'experiment_xml',
                    required = True,
                    help = 'specify the path to the ENA Experiment metadata file.')
parser.add_argument('-run', '--run-xml', dest = 'run_xml',
                    required = True,
                    help = 'specify the path to the ENA Run metadata file.')
parser.add_argument('-v', '--validate-metadata-only', dest = 'validate_only', action='store_true',
                    help = 'when included, no data will be submitted and only the metadata folder'
                           ' metadata file will be validated.')
parser.add_argument('-d', '--submit-dir', dest = 'submit_dir',
                    help = 'specify the path to the destination ENA submission dropbox folder')
parser.add_argument('-?', '--help', action = 'help')
args = parser.parse_args()

# python emblebi_ena_submit.py -f <indir> -id <sub_id> -sub <sub.xml> -pro <pro.xml> -sam <sam.xml> -exp <exp.xml> -run <run.xml> -d <submit_dir>

# Define the objects we need.
metadata_client = MetadataClient()
loader = TemplateLoader(config.emblebi_ena_submit_properties.templates_dir)

# Parse iPlant Data Store metadata into format usable by the submission templates
# metadata = metadata_client.get_metadata(args.metadata_path)

# Create the destination submission directory
submit_dir = args.submit_dir
if not submit_dir:
    #submit_dir = '{0}.{1}'.format(os.environ['IPLANT_USER'], args.submission_id)
    submit_dir = '{0}.{1}'.format('test_user', args.submission_id)
if not os.path.exists(submit_dir):
    os.makedirs(submit_dir)

# The ENA project ID is required if the submission mode is not 'ADD'
if args.submit_mode != 'ADD' and not args.project_accession:
    raise Exception("Could not find a submission ID to use for project update.")

# Generate submission.xml in the submission dir
metadata_template = loader.load('/home/davey/git/emblebi-ena-submit/templates/ENA.run.xml')
submission_path = os.path.join(submit_dir, 'run.xml')
test_metadata = {
    "submission_id": "a5sfd5asfd5asfd",
    "bundle": {
        "runs": [
            {
                "files": [
                    {
                        "name": "sample_name",
                        "filename": "fasta-file1.gz",
                        "md5": "064848455cab44dade17bc5a3414d8b1"
                    },
                    {
                        "name": "sample_name",
                        "filename": "fasta-file2.fgz",
                        "md5": "86913eb52f5f67aaaf711f4c32c2b0c6"
                    }
                ]
            }
        ]
    }
}

stream = metadata_template.generate(metadata=test_metadata, submit_mode=args.submit_mode)
with open(submission_path, 'w') as f:
    stream.render(method='xml', out=f)

# Validate generated XML
#xml_validator = EnaXmlValidator(config.emblebi_ena_submit_properties.schemas_dir,
#                                config.emblebi_ena_submit_properties.submission_schema_path,
#                                config.emblebi_ena_submit_properties.study_schema_path,
#                                config.emblebi_ena_submit_properties.sample_schema_path,
#                                config.emblebi_ena_submit_properties.experiment_schema_path,
#                                config.emblebi_ena_submit_properties.run_schema_path)
#xml_validator.validate_ena_xml(submission_path)

if args.validate_only or not args.input_dir:
    print("Only validated metadata, no data was submitted to the NCBI SRA.")
else:
    uploader = EnaDataFileUploader(config.emblebi_ena_submit_properties.ascp_cmd,
                                  config.emblebi_ena_submit_properties.ena_user,
                                  config.emblebi_ena_submit_properties.ena_host,
                                  config.emblebi_ena_submit_properties.ena_sumbit_path)

    # Build the list of submission input file paths for the uploader
    input_paths = metadata_client.get_bio_project_file_paths(test_metadata, args.input_dir)
    print(input_paths)
    # uploader.upload_datafiles(submit_dir, input_paths)
