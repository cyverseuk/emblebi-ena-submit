### EMBL-EBI ENA Submission

#### Description and Quick Start

Publish data to the EMBL-EBI European Nucleotide Archive.
See https://pods.iplantcollaborative.org/wiki/pages/viewpage.action?pageId=20351132 for a description of the individual Apps and submission workflow.

#### Input File(s)

A JSON metadata fragment is required that describes the list of files present in the CyVerse UK Data Store that you want to submit.
The appropriate metadata should be supplied as 4 ENA XML files, i.e. submission, project, experiment and sample.
There is a run file Metadata Template available that will be populated with the CyVerse filename and md5 metadata.

#### Outputs

This App will generate a folder, named with the username of the submitter and the submission ID,
which contains all the required XML files generated from the given metadata input file.
These XMLs files are submitted to the ENA along with the compressed data files.

Aspera Connect manifests and transfer log files will be returned with other job log files in the `logs` output folder.
