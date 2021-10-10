import os
from HSDFinder import settings
from . import pfam

FILE_ROOT = os.path.join(settings.MEDIA_ROOT, 'upload')


def fun1(content, s_length, filter):
    lines = content.split('\n')
    result = pfam.step(lines, filter, s_length, 'text')
    return result


def pfam_fun(content, pfam_content, filter, s_length, find_type):
    lines = content.split('\n')
    pfam_lines = pfam_content.split('\n')
    output = pfam.step(lines, filter, s_length, 'file')
    if isinstance(output, str) and output.startswith("Error:"):
        return output
    result = pfam.pfam_to_oneline(pfam_lines, output, find_type, 'text', '_')
    return result


def file_fun1(file_name, filter, s_length, output_type):
    pathname = os.path.join(FILE_ROOT, file_name)
    with open(pathname, 'r', encoding='utf8') as f:
        lines = f.readlines()

    result = pfam.step(lines, filter, s_length, output_type)
    if isinstance(result, str) and result.startswith("Error:"):
        return result
    result_filename = pfam.out_file_name(file_name)
    result_pathname = os.path.join(FILE_ROOT, result_filename)
    with open(result_pathname, 'w') as f:
        f.write(result)
    return result_filename


def pfam_file_fun(file_name, filter,  s_length, file_output_type, pfam_filename, find_type):
    pathname = os.path.join(FILE_ROOT, file_name)
    pfam_pathname = os.path.join(FILE_ROOT, pfam_filename)
    with open(pathname, 'r', encoding='utf8') as f:
        lines = f.readlines()
    with open(pfam_pathname, 'r', encoding='utf8') as f2:
        lines_pfam = f2.readlines()
    output = pfam.step(lines, filter, s_length, file_output_type)
    if isinstance(output, str) and output.startswith("Error:"):
        return output
    result = pfam.pfam_to_oneline(lines_pfam, output, find_type, file_output_type, pfam_filename)
    return result
