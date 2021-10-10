from django.shortcuts import render
from django.http import StreamingHttpResponse
import os
from . import operation
from HSDFinder import settings
from collections import defaultdict
from . import models
from django.http import JsonResponse

FILE_ROOT = os.path.join(settings.MEDIA_ROOT, 'upload')


def home(request):
    faqs = models.QandA.objects.all()
    videos = models.Item.objects.all()
    return render(request, "index.html", {'faqs': faqs, 'head_video':videos[5],'videos': videos[0:3],'videos_db': videos[3:5]})


def submit(request):
    ctx = {}
    if request.is_ajax():
        try:
            # text input
            text_content = request.POST['up_text']
            text_content_pfam = request.POST['up_text_pfam']
            filter = select_filter(request.POST['filter'])
            find_type = request.POST['dropdown']
            s_length = int(request.POST['length'])
            if text_content and not text_content_pfam:
                # run
                out_result = operation.fun1(text_content, filter, s_length)
                if out_result.startswith("error:"):
                    ctx['error'] = out_result
                else:
                    out_result = out_result.replace('\n', '<br>')
                    out_result = out_result.replace('\t', '&emsp;')
                    ctx['output_text'] = out_result
            elif text_content and text_content_pfam:
                out_result = operation.pfam_fun(text_content, text_content_pfam, filter, s_length, find_type)
                out_result = out_result.replace('\n', '<br>')
                out_result = out_result.replace('\t', '&emsp;')
                if out_result == "":
                    out_result = "No HSD Found."
                if out_result.startswith("error:"):
                    ctx['error'] = out_result
                else:
                    ctx['output_text'] = out_result
            # file input
            file_obj = request.FILES.get("up_file")
            pfam_file = request.FILES.get("up_file_PFAM")
            if file_obj:
                output = ''
                pathname = os.path.join(FILE_ROOT, file_obj.name)
                with open(pathname, 'wb+') as destination:
                    for chunk in file_obj.chunks():
                        destination.write(chunk)
                if not pfam_file:
                    output = operation.file_fun1(file_obj.name, filter, s_length, "text")
                # if pfam file exists
                elif pfam_file:
                    pathname_pfam = os.path.join(FILE_ROOT, pfam_file.name)
                    with open(pathname_pfam, 'wb+') as destination:
                        for chunk in pfam_file.chunks():
                            destination.write(chunk)
                    output = operation.pfam_file_fun(file_obj.name, filter, s_length, "file", pfam_file.name, find_type)
                # output file name
                if output.startswith("error:"):
                    ctx['error'] = output
                else:
                    ctx['filename'] = output
        except Exception as e:
            ctx['error'] = str(e) + ". Incorrect input file format."
    if not ctx:
        ctx['error'] = "No input text or file."
    return JsonResponse(ctx)


def heatmap(request):
    if request.is_ajax():
        import pandas as pd
        import matplotlib.pyplot as plt
        import numpy as np
        import base64
        import time
        from io import BytesIO
        hsd_file_list = request.FILES.getlist('hsd_file')
        ko_file_list = request.FILES.getlist('ko_file')
        org_name_list = request.POST.getlist('organism_name')
        result = pd.DataFrame(columns=('category1', 'category2', 'ko_id', 'function', 'species_name',
                                       'hsds_id', 'hsds_num'))
        if len(hsd_file_list)==0:
            return JsonResponse({'error_heatmap': 'No input file.'})
        try:
            row = float(request.POST['input_row'])
            col = float(request.POST['input_col'])
        except ValueError:
            return JsonResponse({'error_heatmap': 'The figure size should be a number.'})
        for i in range(len(hsd_file_list)):
            try:
                hsd_file = hsd_file_list[i]
                ko_file = ko_file_list[i]
                org_name = org_name_list[i]
            except IndexError:
                return JsonResponse({'error_heatmap': 'The number of input files or organism names not match.'})
            if org_name == '':
                return JsonResponse({'error_heatmap': 'Organism names cannot be empty.'})
            # read hsd and gene pairs
            hsd_dic = defaultdict(list)
            hsd_content = hsd_file.read()
            hsd_content = str(hsd_content, encoding="utf-8")
            hsd_lines = hsd_content.split('\n')
            for hsd_line in hsd_lines:
                if not hsd_line == '':
                    h_items = hsd_line.split('\t')
                    if len(h_items) > 1:
                        genes = h_items[1].split('; ')
                        for gene in genes:
                            hsd_dic[gene].append(h_items[0])
            # read ko numbers with genes
            ko_content = ko_file.read()
            ko_content = str(ko_content, encoding="utf-8")
            g_dic = defaultdict(list)
            ko_lines = ko_content.split('\n')
            for ko_line in ko_lines:
                if not ko_line == '':
                    k_items = ko_line.split('\t')
                    if len(k_items) > 1:
                        g_dic[k_items[1]].append(k_items[0])
            # read ko information from database
            keggs = models.KO.objects.all().order_by('category2')
            for kegg in keggs:
                if kegg.ko_number in g_dic.keys():
                    temp = []
                    for g in g_dic[kegg.ko_number]:
                        if g in hsd_dic.keys():
                            temp += hsd_dic[g]
                    temp = list(set(temp))
                    hsd_num = len(temp)
                    if hsd_num > 0:
                        ko_name = kegg.description.split('[EC')[0]
                        ko_name = kegg.ko_number + '  ' + ko_name
                        result = result.append(pd.DataFrame({'category1': [kegg.category1], 'category2': [kegg.category2],
                                                             'ko_id': [ko_name], 'species_name': [org_name],
                                                             'hsds_id': [', '.join(temp)], 'hsds_num': [hsd_num]}),
                                               ignore_index=True)
        if len(hsd_file_list) > 0:
            # draw heatmap
            threshold = 1
            if len(hsd_file_list) > 1:
                threshold = 2
            # if len(hsd_file_list) > 3:
            #     threshold = 3
            heatmap_data = pd.pivot_table(result, index=['ko_id', 'category2'],
                                          columns='species_name', values='hsds_num', aggfunc='first')
            heatmap_data.reset_index(level=['category2'], inplace=True)
            heatmap_data = heatmap_data.dropna(thresh=threshold)
            heatmap_data = heatmap_data.fillna(0)
            cmap = "magma_r"
            category = heatmap_data.pop("category2")
            try:
                fig= plt.figure(figsize=(row, col))
                # Plot the heatmap
                ax = fig.add_axes([0.125, 0, 0.85, 1])
                im = ax.pcolor(heatmap_data, cmap=cmap, edgecolors='w', linewidths=1)
                ax.yaxis.tick_right()
                ax.yaxis.set_label_position("right")
                plt.yticks(np.arange(0.5, len(heatmap_data.index), 1), heatmap_data.index, fontsize=7)
                plt.xticks(np.arange(0.5, len(heatmap_data.columns), 1), heatmap_data.columns, fontstyle='italic')
                plt.setp(ax.get_xticklabels(), rotation=60, ha="right", rotation_mode="anchor")
                # fig.subplots_adjust(left=0.5)
                cbar_ax = fig.add_axes([0.025, 0.25, 0.02, 0.5])
                fig.colorbar(im, cax=cbar_ax)
                # fig.tight_layout()
            except Exception as e:
                return JsonResponse({'error_heatmap': str(e) + '. '})
            save_name = 'heatmap_' + '_'.join(org_name_list) + "_" + time.strftime('%Y%m%d%H%M%S') + '.eps'
            save_path = os.path.join(FILE_ROOT, save_name)
            save_file_name = 'heatmap_' + '_'.join(org_name_list) + "_" + time.strftime('%Y%m%d%H%M%S') + '.tsv'
            save_file_path = os.path.join(FILE_ROOT, save_file_name)
            result.to_csv(save_file_path, sep='\t')
            # change plt to html
            buffer = BytesIO()
            plt.savefig(buffer, bbox_inches='tight')
            plot_data = buffer.getvalue()
            imb = base64.b64encode(plot_data)  # encode plot_data
            ims = imb.decode()
            imd = "data:image/png;base64," + ims
            plt.savefig(save_path, bbox_inches='tight')
            return JsonResponse({"img": imd, "path": save_name, "file_path": save_file_name})
    return render(request, "index.html", {})


def select_filter(index):
    # convert selected option index to str
    if index == '100%':
        return 100.0
    elif index == '90%':
        return 90.0
    elif index == '80%':
        return 80.0
    elif index == '70%':
        return 70.0
    elif index == '60%':
        return 60.0
    elif index == '50%':
        return 50.0
    elif index == '40%':
        return 40.0
    elif index == '30%':
        return 30.0
    else:
        return 100.0


def file_iterator(file_name, chunk_size=512):
    with open(file_name) as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break


def download(request, filename):
    file_pathname = os.path.join(FILE_ROOT, filename)
    response = StreamingHttpResponse(file_iterator(file_pathname))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(filename)

    return response


def example_download(request, filename):
    print(filename)
    file_pathname = os.path.join(settings.MEDIA_ROOT, filename)
    if filename.split('.')[-1] == 'pdf' or filename.split('.')[-1] == 'zip':
        file = open(file_pathname, 'rb')
        response = StreamingHttpResponse(file)
    else:
        response = StreamingHttpResponse(file_iterator(file_pathname))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(filename)

    return response

