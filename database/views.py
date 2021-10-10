from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import StreamingHttpResponse
from django.http import JsonResponse
from HSDFinder import settings
from collections import defaultdict
import os
import time
from . import models
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage
from json import JSONEncoder
from fileOperation.models import Item
from django.core.exceptions import ObjectDoesNotExist

FILE_ROOT = os.path.join(settings.MEDIA_ROOT, 'upload')
DB_ROOT = os.path.join(settings.MEDIA_ROOT, 'db')


class HSDOutput:
    def __init__(self, h_id, name, genes, num):
        self.h_id = h_id
        self.name = name
        self.genes = genes
        self.num = num


class HSDOutputEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


class GeneItem:
    def __init__(self, id, name, length, pf_num, pf_domain, ipr, ipr_domain, seq):
        self.id = id
        self.name = name
        self.length = length
        self.pf_num = pf_num
        self.pf_domain = pf_domain
        self.ipr = ipr
        self.ipr_domain = ipr_domain
        self.seq = seq


class BlastResult:
    def __init__(self, query, seq, hsds, per, overlap, mismatch, gapopen, qstart, qend, sstart, send, evalue, bitscore):
        self.query = query
        self.seq = seq
        self.hsds = hsds
        self.per = per
        self.overlap = overlap
        self.mismatch = mismatch
        self.gapopen = gapopen
        self.qstart = qstart
        self.qend = qend
        self.sstart = sstart
        self.send = send
        self.evalue = evalue
        self.bitscore = bitscore


class NcbiGI:
    def __init__(self, name, accession, start, stop, strand):
        self.name = name
        self.accession = accession
        self.start = start
        self.stop = stop
        self.strand = strand


class Kegg:
    def __init__(self, ct1, ct, ko, des, organism, gene_list, hsd):
        self.ct1 = ct1
        self.ct = ct
        self.ko = ko
        self.des = des
        self.organism = organism
        self.gene_list = gene_list
        self.hsd = hsd


class QandA:
    def __init__(self, t, q, a):
        self.t = t
        self.q = q
        self.a = a


def index(request):
    return render(request, "database.html", {})


def search(request):
    return render(request, 'Search.html', {})


def look(request):
    result_list = []
    if request.is_ajax():
        name = request.POST['hsdid']
        category = request.POST['category']
        if category == 'All':
            hsds_list = models.Hsds.objects.filter(Q(name__icontains=name) | Q(genes_list__icontains=name)).order_by(
                'name')
        else:
            category = category.lower()
            hsds_list = models.Hsds.objects.filter(species__category=category).filter(
                Q(name__icontains=name) | Q(genes_list__icontains=name)).order_by('name')
        paginator = Paginator(hsds_list, 30)
        page = int(request.POST['page_now'])
        try:
            hsds = paginator.page(page)
        except PageNotAnInteger:
            hsds = paginator.page(1)
        except InvalidPage:
            hsds = paginator.page(paginator.num_pages)
        hsds_li = list(hsds.object_list.values())
        for item in hsds_li:
            num = len(item['genes_list'].split('; '))
            result_list.append(HSDOutputEncoder().encode(HSDOutput(item['id'], item['name'], item['genes_list'], num)))
        page_range = page_num_cal(9, paginator.num_pages, page)
        page_total = hsds.paginator.num_pages
        page_previous = 0
        page_next = 0
        if hsds.has_previous():
            page_previous = hsds.previous_page_number()
        if hsds.has_next():
            page_next = hsds.next_page_number()
        num = len(hsds_list)
        ctx = {'hsds': result_list,
               'num': num,
               'page_now': page,
               'page_total': page_total,
               'page_range': list(page_range),
               'page_has_p': hsds.has_previous(),
               'page_has_n': hsds.has_next(),
               'page_p': page_previous,
               'page_n': page_next}
        return JsonResponse(ctx)
    return render(request, 'Search.html', {})


def browse(request):
    p_files = models.Files.objects.order_by('name').filter(category__in=['plant'])
    a_files = models.Files.objects.order_by('name').filter(category__in=['animal'])
    b_files = models.Files.objects.order_by('name').filter(category__in=['bacteria'])
    ctx = {'plant_files': p_files, 'animal_files': a_files, 'bacteria_files': b_files}
    return render(request, 'browse.html', ctx)


def hsd(request, species_id, page):
    hsds_list = models.Hsds.objects.filter(species_id=species_id)
    file = models.Files.objects.get(id=species_id)
    paginator = Paginator(hsds_list, 50)
    try:
        hsds = paginator.page(page)
    except PageNotAnInteger:
        hsds = paginator.page(1)
    except InvalidPage:
        hsds = paginator.page(paginator.num_pages)
    hsds_li = list(hsds.object_list.values())
    result_list = []
    for item in hsds_li:
        num = len(item['genes_list'].split('; '))
        result_list.append(HSDOutput(item['id'], item['name'], item['genes_list'], num))
    page_range = page_num_cal(11, paginator.num_pages, page)
    page_total = hsds.paginator.num_pages
    page_previous = 0
    page_next = 0
    if hsds.has_previous():
        page_previous = hsds.previous_page_number()
    if hsds.has_next():
        page_next = hsds.next_page_number()
    ctx = {'hsds': result_list,
           'file': file,
           'page': page,
           'page_total': page_total,
           'page_range': page_range,
           'page_has_p': hsds.has_previous(),
           'page_has_n': hsds.has_next(),
           'page_p': page_previous,
           'page_n': page_next}
    return render(request, 'hsd.html', ctx)


from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from xmltramp2 import xmltramp
import requests


def restRequest(url):
    try:
        req = Request(url)
        # Make the request (HTTP GET).
        reqH = urlopen(req)
        resp = reqH.read()
        contenttype = reqH.info()

        if (len(resp) > 0 and contenttype != u"image/png;charset=UTF-8"
                and contenttype != u"image/jpeg;charset=UTF-8"
                and contenttype != u"application/gzip;charset=UTF-8"):
            try:
                result = str(resp, u'utf-8')
            except UnicodeDecodeError:
                result = resp
        else:
            result = resp
        reqH.close()
    # Errors are indicated by HTTP status codes.
    except HTTPError as ex:
        result = requests.get(url).content
    return result


def serviceGetStatus(jobId):
    baseUrl = 'https://www.ebi.ac.uk/Tools/services/rest/clustalo'
    requestUrl = baseUrl + '/status/' + jobId
    status = restRequest(requestUrl)
    return status


def clientPoll(jobId):
    result = 'PENDING'
    while result == 'RUNNING' or result == 'PENDING':
        result = serviceGetStatus(jobId)
        if result == 'RUNNING' or result == 'PENDING':
            time.sleep(3)


def cluster_omega(request):
    hsd_id = request.POST['hsd_id']
    hsd = models.Hsds.objects.get(id=hsd_id)
    gene = hsd.genes_list.split('; ')
    params = {}
    sequence = ""
    for i in range(len(gene)):
        s_list = models.Genes.objects.filter(species_id_id=hsd.species_id).filter(name=gene[i])
        if len(s_list) > 0:
            seq = s_list[0].sequence
        else:
            seq = "No Sequence found"
        sequence += ">" + gene[i] + "\n" + seq + "\n\n"
    params['email'] = "huyining2019@hotmail.com"
    params['sequence'] = sequence
    params['stype'] = 'protein'
    baseUrl = 'https://www.ebi.ac.uk/Tools/services/rest/clustalo'
    requestUrl = baseUrl + '/run/'
    # Get the data for the other options
    requestData = urlencode(params)
    # Errors are indicated by HTTP status codes.
    jobId = ""
    try:
        req = Request(requestUrl)
        # Make the submission (HTTP POST).
        print(req)
        reqH = urlopen(req, requestData.encode(encoding='utf_8', errors='strict'))
        jobId = str(reqH.read(), 'utf-8')
        reqH.close()
        print(jobId)
    except HTTPError as ex:
        print(xmltramp.parse(str(ex.read(), u'utf-8'))[0][0])
        quit()
    if not jobId == "":
        clientPoll(jobId)
        requestUrl = baseUrl + u'/result/' + jobId + u'/' + 'aln-clustal_num'
        requestUrl_pim = baseUrl + u'/result/' + jobId + u'/' + 'pim'
        result = restRequest(requestUrl)
        pim = restRequest(requestUrl_pim)
        return JsonResponse({'result': result + pim})


def hsd_detail(request, hsd_id):
    hsd = models.Hsds.objects.get(id=hsd_id)
    result = []
    gene = hsd.genes_list.split('; ')
    length = hsd.lengths.split('; ')
    pf = hsd.pf_num.split('; ')
    domain1 = hsd.description.split('; ')
    ipr = hsd.ipr.split('; ')
    domain2 = hsd.domain.split('; ')
    sequence = ""
    ncbi = []
    have_ncbi = 0
    for i in range(len(gene)):
        s_list = models.Genes.objects.filter(species_id_id=hsd.species_id).filter(name=gene[i])
        g_id = 0
        if len(s_list) > 0:
            seq = s_list[0].sequence
            g_id = s_list[0].id
            try:
                ncbi_gi = models.Ncbi_ID.objects.get(gene_id_id=g_id)
                strand = "true" if ncbi_gi.strand == '-' else "false"
                ncbi.append(NcbiGI(ncbi_gi.name, ncbi_gi.accession, ncbi_gi.start, ncbi_gi.stop, strand))
                have_ncbi += 1
            except ObjectDoesNotExist:
                pass
        else:
            seq = "No Sequence found"
        sequence += ">" + gene[i] + "\n" + seq + "\n\n"
        pf_items = pf[i].split(', ') if len(pf) > i and len(pf[i]) > 0 else []
        pf_html = []
        for pf_item in pf_items:
            pf_html.append('<a href="https://pfam.xfam.org/family/' + pf_item + '" style="text-decoration: underline">'
                           + pf_item + '</a>')
        ipr_items = ipr[i].split(', ') if len(ipr) > i and len(ipr[i]) > 1 else []
        ipr_html = []
        for ipr_item in ipr_items:
            ipr_html.append('<a href="http://www.ebi.ac.uk/interpro/entry/InterPro/' + ipr_item +
                            '" style="text-decoration: underline">' + ipr_item + '</a>')
        result_length = length[i] if len(length) > i else "unknown"
        result_domain1 = domain1[i] if len(domain1) > i and len(domain1[i]) > 0 else ""
        result_domain2 = domain2[i] if len(domain2) > i and len(domain2[i]) > 0 else ""
        result.append(GeneItem(g_id, gene[i], result_length, ", ".join(pf_html), result_domain1, ", ".join(ipr_html), result_domain2, seq))
    # align = cluster_omega(sequence)
    # align = align.replace('\n', '<br>')
    ctx = {'hsd': hsd.name, 'hsd_id': hsd_id, 'genes': result, 'active_tab': 'Genome', 'ncbi': ncbi,
           'have_ncbi': have_ncbi}
    # 'align': align}
    return render(request, 'hsd_detail.html', ctx)


def blast(request):
    cat = models.Files.objects.values_list('category', flat=True).distinct().order_by('category')
    species = models.Files.objects.filter(category__in=['plant', 'animal']).values_list('name', flat=True).distinct().order_by('name')
    if request.is_ajax():
        organism = request.POST['species']
        algorithm = request.POST['algorithm']
        e_value = request.POST['e_value']
        m_target = request.POST['m_target']
        print(organism + '\t' + algorithm + '\t' + e_value + '\t' + m_target)
        file_obj = request.FILES.get("up_file")
        seq = request.POST['up_text']
        # get file name
        filename = ''
        pathname = ''
        if file_obj:
            filename = file_obj.name
            pathname = os.path.join(FILE_ROOT, file_obj.name)
            with open(pathname, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)
        elif seq:
            filename = time.strftime('%Y%m%d%H%M%S')
            pathname = os.path.join(FILE_ROOT, "seq" + filename + '.fa')
            with open(pathname, 'w') as destination:
                destination.write(seq)
        else:
            return JsonResponse({'error': 'No input sequence.'})
        # get database path
        db_list = []
        if organism == 'All Organisms':
            db_list.append("mydb.fasta")
        elif organism in cat:
            dbs = models.Files.objects.filter(category=organism)
            for d in dbs:
                db_list.append(d.db_name)
        elif organism in species:
            dbs = models.Files.objects.filter(name=organism)
            db_list.append(dbs[0].db_name)
        else:
            return JsonResponse({'error': 'Organism not found.'})
        # start blast
        import subprocess
        result_list = []
        for db_name in db_list:
            db = os.path.join(DB_ROOT, db_name)
            output_path = os.path.join(FILE_ROOT, db_name + filename + ".xml")
            p = subprocess.Popen(algorithm.lower() + ' -out ' + output_path + ' -outfmt ' + str(6) +
                                 ' -query ' + pathname + ' -db ' + db + ' -evalue '
                                 + e_value + ' -max_target_seqs ' + m_target,
                                 shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = p.communicate()
            with open(output_path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip('\n')
                    i = line.split('\t')
                    if len(i) > 11:
                        gene_name = '_'.join(i[1].split('_')[:-1])
                        species_id = int(i[1].split('_')[-1])
                        hsd_name_dic = models.Hsds.objects.filter(species_id=species_id).filter(
                            genes_list__contains=gene_name)
                        result_hsd_html = '<td style="width: 10%">'
                        for item in hsd_name_dic:
                            if gene_name in item.genes_list.split('; '):
                                result_hsd_html += '<a href="/database/hsd_detail/' + str(
                                    item.id) + '">' + item.name + '</a><br>'
                        gene_name = '<a href="https://www.ncbi.nlm.nih.gov/protein/' + gene_name\
                                    + '"/ style="text-decoration: underline">' + gene_name + '</a>'
                        result_hsd_html += '</td>'
                        result_html = '<tr><td style="width: 10%">' + i[
                            0] + '</td><td style="width: 10%">' + gene_name + '</td>' + result_hsd_html + \
                                      '<td style="width: 7%">' + i[2] + '</td><td style="width: 7%">' + i[
                                          3] + '</td><td style="width: 7%">' + i[4] + \
                                      '</td><td style="width: 7%">' + i[5] + '</td><td style="width: 7%">' + i[
                                          6] + '</td><td style="width: 7%">' + i[7] + \
                                      '</td><td style="width: 7%">' + i[8] + '</td><td style="width: 7%">' + i[
                                          9] + '</td><td style="width: 7%">' + i[10] + \
                                      '</td><td style="width: 7%">' + i[11] + '</td>'
                        result_list.append(result_html)
        return JsonResponse({'length': len(result_list), 'results': result_list})
    return render(request, 'Blast.html', {'cat': cat, 'species': species})


def heatmap(request):
    species = models.Files.objects.filter(category__in=['plant', 'animal']).values_list('name', flat=True).distinct().order_by('name')
    if request.POST:
        import pandas as pd
        import seaborn as sns
        import matplotlib.pyplot as plt
        import matplotlib.colors as cls
        import base64
        from io import BytesIO
        selected = request.POST.getlist("select_species")
        method = request.POST['method']
        metric = request.POST['metric']
        cluster = request.POST.getlist('select_cluster')
        standard = request.POST.getlist('select_standard')
        row_size = int(request.POST['input_row'])
        col_size = int(request.POST['input_col'])
        # check cluster the row and col or not
        row_cluster = False
        col_cluster = False
        for i in cluster:
            if i == 'row':
                row_cluster = True
            elif i == 'col':
                col_cluster = True
        # method and metric
        method = method.lower()
        metric = metric.lower()
        # standard
        if len(standard) == 0:
            standard = None
        elif standard[0] == 'row':
            standard = 0
        elif standard[0] == 'col':
            standard = 1
        # prepare data
        items = models.KEGG.objects.filter(species__in=selected)
        result = pd.DataFrame(columns=('ko_num', 'function', 'category', 'species_name', 'hsds_num'))
        for item in items:
            result = result.append(pd.DataFrame({'ko_num': [item.ko_num], 'function': [item.description],
                                                 'category': [item.class_two], 'species_name': [item.species],
                                                 'hsds_num': [item.hsd_num]}), ignore_index=True)
        heatmap_data = pd.pivot_table(result, index=['ko_num', 'function', 'category'],
                                      columns='species_name', values='hsds_num', aggfunc='first')
        heatmap_data.reset_index(level=['category'], inplace=True)
        threshold = 2
        if len(selected) > 3:
            threshold = 3
        heatmap_data = heatmap_data.dropna(thresh=threshold)
        heatmap_data = heatmap_data.fillna(0)
        heatmap_data.sort_values(by='category', inplace=True)
        category = heatmap_data.pop("category")
        lut = dict(zip(category.unique(), cls.CSS4_COLORS))
        row_colors = category.map(lut)
        cmap = sns.cubehelix_palette(light=1, as_cmap=True)
        cm = sns.clustermap(heatmap_data, method=method.lower(), metric=metric.lower(), standard_scale=standard,
                            row_cluster=row_cluster, col_cluster=col_cluster, robust=True,
                            figsize=(row_size, col_size), dendrogram_ratio=[0.2, 0.25],
                            row_colors=row_colors, cmap=cmap, center=1)
        plt.setp(cm.ax_heatmap.yaxis.get_majorticklabels(), fontsize=8)
        save_name = 'heatmap_' + '_'.join(selected) + '.eps'
        save_path = os.path.join(settings.MEDIA_ROOT, save_name)
        # change plt to html
        buffer = BytesIO()
        plt.savefig(buffer)
        plot_data = buffer.getvalue()
        imb = base64.b64encode(plot_data)  # encode plot_data
        ims = imb.decode()
        imd = "data:image/png;base64," + ims
        plt.savefig(save_path)
        return render(request, 'kegg.html', {'species': species, "img": imd, "path": save_name,
                                             'active_tab': 'heatmap'})
    return render(request, 'kegg.html', {'species': species, 'active_tab': 'kegg'})


def kegg(request):
    species = models.Files.objects.filter(category__in=['plant', 'animal']).values_list('name', flat=True).distinct().order_by('name')
    if request.is_ajax():
        sss = request.POST['species']
        if not sss == '':
            results_list = models.KEGG.objects.filter(species__name=sss).order_by('class_one')
            paginator = Paginator(results_list, 30)
            page = int(request.POST['page_now'])
            try:
                results = paginator.page(page)
            except PageNotAnInteger:
                results = paginator.page(1)
            except InvalidPage:
                results = paginator.page(paginator.num_pages)
            results_li = list(results.object_list.values())
            keggs = defaultdict(list)
            for result in results_li:
                o_names = result['hsd_original_name'].split(', ')
                hsds_list = []
                for name in o_names:
                    hsds = models.Hsds.objects.filter(name=name)
                    hsds_list.extend(hsds)
                hsds_list = list(set(hsds_list))
                species_temp = models.Files.objects.filter(id=result['species_id'])
                species_name = species_temp[0].name
                keggs[result['class_one']].append(Kegg(result['class_one'], result['class_two'], result['ko_num'],
                                                       result['description'], species_name, result['genes_list'],
                                                       hsds_list))
            output_html = {}
            for k in keggs.keys():
                html = '<td style="width: 12%" rowspan="' + str(len(keggs[k])) + '">' + k + '</td>'
                for kegg_item in keggs[k]:
                    html += '<td style="width: 22%">' + kegg_item.ct + '</td><td style="width: 7%">' \
                                                                       '<a href="https://www.genome.jp/entry/' + \
                            kegg_item.ko + '" style="text-decoration: underline">' + kegg_item.ko + \
                            '</a></td><td style="width: 25%">' + kegg_item.des + '</td><td style="width: 17%">' + \
                            kegg_item.gene_list + '</td><td style="width: 17%">'
                    for hsd_item in kegg_item.hsd:
                        html += '<a href="/database/hsd_detail/' + str(hsd_item.id) + '">' + hsd_item.name + '</a><br>'
                    html += '</td></tr><tr>'
                output_html[k] = html
            keggs.clear()
            page_range = page_num_cal(11, paginator.num_pages, page)
            page_total = results.paginator.num_pages
            page_previous = 0
            page_next = 0
            if results.has_previous():
                page_previous = results.previous_page_number()
            if results.has_next():
                page_next = results.next_page_number()
            ctx = {'keggs': output_html,
                   'active_tab': 'kegg',
                   'page_now': page,
                   'page_total': page_total,
                   'page_range': list(page_range),
                   'page_has_p': results.has_previous(),
                   'page_has_n': results.has_next(),
                   'page_p': page_previous,
                   'page_n': page_next}
            return JsonResponse(ctx)
    return render(request, 'kegg.html', {'species': species, 'active_tab': 'kegg'})


def faq(request):
    faqs = models.Faq.objects.all()
    types = models.Faq.objects.values('type').distinct().order_by('type')
    r_dic = {}
    for t in types:
        r_dic[t['type']] = []
    for faq in faqs:
        r_dic[faq.type].append(QandA(faq.id, faq.question, faq.answer))
    videos = Item.objects.all()
    return render(request, 'faq.html', {'faqs': r_dic, 'head_video': videos[5], 'videos_db': videos[3:5]})


def back(request):
    return HttpResponseRedirect('/')


def file_iterator(file_name, chunk_size=512):
    with open(file_name) as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break


def download(request, fileid):
    file_temp = models.Files.objects.get(id=fileid)
    filename = file_temp.file_name
    file_pathname = os.path.join(settings.MEDIA_ROOT, filename)
    response = StreamingHttpResponse(file_iterator(file_pathname))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(filename)

    return response


def hsd_download(request, filename, hsd_id):
    hsds = models.Hsds.objects.get(id=hsd_id)
    species_name = models.Files.objects.get(id=hsds.species_id)
    filename = species_name.name + '_' + filename
    pathname = os.path.join(FILE_ROOT, filename)
    gene = hsds.genes_list.split('; ')
    sequence = ""
    for i in range(len(gene)):
        s_list = models.Genes.objects.filter(species_id_id=hsds.species_id).filter(name=gene[i])
        if len(s_list) > 0:
            seq = s_list[0].sequence
        else:
            seq = "No Sequence found"
        sequence += ">" + gene[i] + "\n" + seq + "\n"
    with open(pathname, 'w') as destination:
        destination.write(hsds.name + '\t' + hsds.genes_list + '\t' + hsds.lengths + '\t' +
                          hsds.type + '\t' + hsds.pf_num + '\t' + hsds.description + '\t' +
                          hsds.ipr + '\t' + hsds.domain + '\n\n')
        destination.write(sequence)
    response = StreamingHttpResponse(file_iterator(pathname))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(filename)

    return response


def heatmap_download(request, filename):
    file_pathname = os.path.join(settings.MEDIA_ROOT, filename)
    response = StreamingHttpResponse(file_iterator(file_pathname))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(filename)

    return response


def page_num_cal(max_page_num, total_page, current_page):
    half_page_num = max_page_num // 2
    if max_page_num >= total_page:
        start_page = 1
        end_page = total_page
    elif current_page + half_page_num >= total_page:
        end_page = total_page
        start_page = total_page - max_page_num
    elif current_page - half_page_num <= 1:
        start_page = 1
        end_page = max_page_num
    else:
        start_page = current_page - half_page_num
        end_page = current_page + half_page_num
    page_range = range(start_page, end_page + 1)
    return page_range
