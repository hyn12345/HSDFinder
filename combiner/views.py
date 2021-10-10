from django.shortcuts import render
import pandas as pd
from collections import defaultdict
import os
import time
from HSDFinder import settings
from django.http import JsonResponse


FILE_ROOT = os.path.join(settings.MEDIA_ROOT, 'upload')


class Des:
    def __init__(self, g_type, length, hit_des, hit_name, p_id, e_value):
        self.g_type = g_type
        self.length = length
        self.hit_des = hit_des
        self.hit_name = hit_name
        self.p_id = p_id
        self.e_value = e_value


class Pfam:
    def __init__(self, name, ftype, pf, domain1, value, ipr, domain2):
        self.name = name
        self.ftype = ftype
        self.pf = pf
        self.domain1 = domain1
        self.value = value
        self.ipr = ipr
        self.domain2 = domain2


def index(request):
    return render(request, "Nobadname.html", {})


def submit(request):
    ctx = {}
    if request.is_ajax():
        ncbi_file = request.FILES.get('ncbi_file')
        swiss_file = request.FILES.get('swiss_file')
        gene_file = request.FILES.get('gene_file')
        ko_file = request.FILES.get('ko_file')
        pfam_file = request.FILES.get('pfam_file')
        selected = request.POST['dropdown']
        output = pd.DataFrame(columns=('Gene', 'Length', 'NoBadName_Hit_Des', 'NoBadName_Hit_Name',
                                       'NoBadName_%ID', 'NoBadName_eValue', 'NCBI_Hit_Des', 'NCBI_Hit_Name',
                                       'NCBI_%ID', 'NCBI_eValue', 'Swiss_Hit_Des', 'Swiss_Hit_Name',
                                       'Swiss_%ID', 'Swiss_eValue'))
        if ncbi_file and swiss_file and gene_file:
            try:
                ncbi_content = ncbi_file.read()
                ncbi_content = str(ncbi_content, encoding="utf-8")
            except Exception as e:
                ctx['error'] = str(e) + '. Failed to read NCBI file.'
                return JsonResponse(ctx)
            try:
                swiss_content = swiss_file.read()
                swiss_content = str(swiss_content, encoding="utf-8")
            except Exception as e:
                ctx['error'] = str(e) + '. Failed to read Swiss file.'
                return JsonResponse(ctx)
            try:
                gene_content = gene_file.read()
                gene_content = str(gene_content, encoding="utf-8")
            except Exception as e:
                ctx['error'] = str(e) + '. Failed to read Gene List file.'
                return JsonResponse(ctx)
            gene_dic = defaultdict(list)
            # load ncbi data
            ncbi_lines = ncbi_content.split('\n')
            for ncbi_line in ncbi_lines:
                ncbi_items = ncbi_line.split('\t')
                if len(ncbi_items) > 13:
                    gene_dic[ncbi_items[0]].append(Des('ncbi', ncbi_items[1], ncbi_items[2], ncbi_items[3],
                                                       ncbi_items[7], ncbi_items[8]))
            # load swiss data
            swiss_lines = swiss_content.split('\n')
            for swiss_line in swiss_lines:
                swiss_items = swiss_line.split('\t')
                if len(swiss_items) > 13:
                    gene_dic[swiss_items[0]].append(Des('swiss', swiss_items[1], swiss_items[2], swiss_items[3],
                                                        swiss_items[7], swiss_items[8]))
            # no bad name output
            for key, value in gene_dic.items():
                result = value[0]
                ncbi_result = None
                swiss_result = None
                if len(value) > 1:
                    find1 = 0
                    find2 = 0
                    for item in value:
                        if (not "Uncharacterized" in item.hit_des) and (not "hypothetical" in item.hit_des):
                            result = item
                            find1 = 1
                        elif ("hypothetical" in item.hit_des) and find1 == 0:
                            result = item
                            find2 = 1
                        elif find1 == 0 and find2 == 0:
                            result = item
                        if item.g_type == 'ncbi':
                            ncbi_result = item
                        elif item.g_type == 'swiss':
                            swiss_result = item
                else:
                    result = value[0]
                    if value[0].g_type == 'ncbi':
                        ncbi_result = value[0]
                    elif value[0].g_type == 'swiss':
                        swiss_result = value[0]
                if ncbi_result and swiss_result:
                    output = output.append(pd.DataFrame({'Gene': [key], 'Length': [result.length], 'NoBadName_Hit_Des': [result.hit_des],
                                                         'NoBadName_Hit_Name': [result.hit_name], 'NoBadName_%ID': [result.p_id],
                                                         'NoBadName_eValue': [result.e_value], 'NCBI_Hit_Des': [ncbi_result.hit_des],
                                                         'NCBI_Hit_Name': [ncbi_result.hit_name], 'NCBI_%ID': [ncbi_result.p_id],
                                                         'NCBI_eValue': [ncbi_result.e_value], 'Swiss_Hit_Des': [swiss_result.hit_des],
                                                         'Swiss_Hit_Name': [swiss_result.hit_name], 'Swiss_%ID': [swiss_result.p_id],
                                                         'Swiss_eValue': [swiss_result.e_value]}), ignore_index=True)
                elif ncbi_result:
                    output = output.append(pd.DataFrame({'Gene': [key], 'Length': [result.length], 'NoBadName_Hit_Des': [result.hit_des],
                                                         'NoBadName_Hit_Name': [result.hit_name], 'NoBadName_%ID': [result.p_id],
                                                         'NoBadName_eValue': [result.e_value], 'NCBI_Hit_Des': [ncbi_result.hit_des],
                                                         'NCBI_Hit_Name': [ncbi_result.hit_name], 'NCBI_%ID': [ncbi_result.p_id],
                                                         'NCBI_eValue': [ncbi_result.e_value]}), ignore_index=True)
                elif swiss_result:
                    output = output.append(pd.DataFrame({'Gene': [key], 'Length': [result.length], 'NoBadName_Hit_Des': [result.hit_des],
                                                         'NoBadName_Hit_Name': [result.hit_name], 'NoBadName_%ID': [result.p_id],
                                                         'NoBadName_eValue': [result.e_value], 'Swiss_Hit_Des': [swiss_result.hit_des],
                                                         'Swiss_Hit_Name': [swiss_result.hit_name], 'Swiss_%ID': [swiss_result.p_id],
                                                         'Swiss_eValue': [swiss_result.e_value]}), ignore_index=True)
            # load gene list
            gene_lines = gene_content.split('\n')
            for gene_line in gene_lines:
                if gene_line not in output['Gene'].values:
                    output = output.append(pd.DataFrame({'Gene': [gene_line]}))
        else:
            ctx['error'] = 'No input file.'
            return JsonResponse(ctx)
        if ko_file or pfam_file:
            from fileOperation import models
            ko_dic = {}
            pfam_output = {}
            if ko_file:
                output['KEGG_KO'] = None
                output['KEGG_Des'] = None
                try:
                    ko_content = ko_file.read()
                    ko_content = str(ko_content, encoding="utf-8")
                except Exception as e:
                    ctx['error'] = str(e) + '. Failed to read KEGG file.'
                    return JsonResponse(ctx)
                ko_lines = ko_content.split('\n')
                for ko_line in ko_lines:
                    ko_items = ko_line.split('\t')
                    if len(ko_items) > 1 and not ko_items[1] == '':
                        ko_dic[ko_items[0]] = ko_items[1]
            # col names
            n_name = selected
            n_no = selected + '_No'
            n_des = selected + '_Des'
            n_evalue = selected + '_evalue'
            if pfam_file:
                # create cols
                output[n_name] = None
                output[n_no] = None
                output[n_des] = None
                output[n_evalue] = None
                output['Interpro_No'] = None
                output['Interpro_domain'] = None
                # read pfam file content
                try:
                    pfam_content = pfam_file.read()
                    pfam_content = str(pfam_content, encoding="utf-8")
                except Exception as e:
                    ctx['error'] = str(e) + '. Failed to read Pfam file.'
                    return JsonResponse(ctx)
                pfam_lines = pfam_content.split('\n')
                pfam_dic = defaultdict(list)
                for pfam_line in pfam_lines:
                    pfam_items = pfam_line.split('\t')
                    if len(pfam_items) > 12 and pfam_items[3].lower() == selected.lower():
                        temp_key = pfam_items[0] + '/' + pfam_items[4]
                        pfam_dic[temp_key].append(Pfam(pfam_items[0], pfam_items[3], pfam_items[4],
                                                       pfam_items[5], pfam_items[8], pfam_items[11],
                                                       pfam_items[12]))
                    elif len(pfam_items) > 10 and pfam_items[3].lower() == selected.lower():
                        temp_key = pfam_items[0] + '/' + pfam_items[4]
                        pfam_dic[temp_key].append(Pfam(pfam_items[0], pfam_items[3], pfam_items[4],
                                                       pfam_items[5], pfam_items[8], '', ''))
                # select the one with smallest value
                d_temp = {}
                for key in pfam_dic.keys():
                    min_index = 0
                    min_value = 99999.0
                    for i in range(len(pfam_dic[key])):
                        try:
                            if float(pfam_dic[key][i].value) < min_value:
                                min_index = i
                                min_value = float(pfam_dic[key][i].value)
                        except ValueError:
                            pass
                    d_temp[key] = pfam_dic[key][min_index]
                pfam_dic.clear()
                # use gene name as key
                pfam_result_dic = defaultdict(list)
                for name in d_temp.keys():
                    gene_name, pf_num = name.split('/')
                    pfam_result_dic[gene_name].append(d_temp[name])
                d_temp.clear()
                # to one line
                for gene in pfam_result_dic.keys():
                    pf_line = ''
                    domain1_line = ''
                    value_line = ''
                    ipr_line = ''
                    domain2_line = ''
                    for n in range(len(pfam_result_dic[gene])):
                        pf_line += pfam_result_dic[gene][n].pf
                        domain1_line += pfam_result_dic[gene][n].domain1
                        value_line += pfam_result_dic[gene][n].value
                        ipr_line += pfam_result_dic[gene][n].ipr
                        domain2_line += pfam_result_dic[gene][n].domain2
                        if n < len(pfam_result_dic[gene]) - 1:
                            pf_line += '; '
                            domain1_line += '; '
                            value_line += '; '
                            ipr_line += '; '
                            domain2_line += '; '
                    pfam_output[gene] = Pfam(gene, selected, pf_line, domain1_line, value_line, ipr_line, domain2_line)
                pfam_result_dic.clear()
            # write to dataframe
            output = output.set_index(['Gene'])
            for g, row in output.iterrows():
                if ko_file:
                    if g in ko_dic.keys():
                        row['KEGG_KO'] = ko_dic[g]
                        des = models.KO.objects.filter(ko_number=ko_dic[g])
                        if len(des)>0:
                            row['KEGG_Des'] = des[0].description
                        else:
                            print(ko_dic[g])
                if pfam_file:
                    if g in pfam_output.keys():
                        row[n_name] = pfam_output[g].ftype
                        row[n_no] = pfam_output[g].pf
                        row[n_des] = pfam_output[g].domain1
                        row[n_evalue] = pfam_output[g].value
                        row['Interpro_No'] = pfam_output[g].ipr
                        row['Interpro_domain'] = pfam_output[g].domain2
            output.reset_index(level=['Gene'], inplace=True)
        save_name = 'NoBadName_Combiner_' + time.strftime('%Y%m%d%H%M%S') + '.tsv'
        save_path = os.path.join(FILE_ROOT, save_name)
        output.to_csv(save_path, sep='\t')
        ctx['filename'] = save_name
    return JsonResponse(ctx)
