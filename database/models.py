from django.db import models


class Files(models.Model):
    name = models.CharField(max_length=100)
    hsds_num = models.IntegerField()
    category = models.CharField(max_length=50)
    description = models.TextField()
    file_name = models.CharField(max_length=100)
    db_name = models.CharField(max_length=100)


class Hsds(models.Model):
    name = models.CharField(max_length=60)
    genes_list = models.TextField()
    lengths = models.TextField()
    type = models.CharField(max_length=30)
    pf_num = models.TextField()
    description = models.TextField()
    ipr = models.TextField()
    domain = models.TextField()
    species = models.ForeignKey('Files', on_delete=models.CASCADE)


class Genes(models.Model):
    name = models.CharField(max_length=100)
    sequence = models.TextField()
    species_id = models.ForeignKey('Files', on_delete=models.CASCADE)


class KEGG(models.Model):
    class_one = models.TextField()
    class_two = models.TextField()
    ko_num = models.CharField(max_length=30)
    description = models.TextField()
    genes_list = models.TextField()
    species = models.ForeignKey('Files', on_delete=models.CASCADE)
    hsd_original_name = models.TextField()
    hsd_num = models.IntegerField()


class Faq(models.Model):
    type = models.CharField(max_length=50)
    question = models.TextField()
    answer = models.TextField()


class Ncbi_ID(models.Model):
    name = models.CharField(max_length=100)
    gene_id = models.ForeignKey('Genes', on_delete=models.CASCADE)
    species_id = models.ForeignKey('Files', on_delete=models.CASCADE)
    accession = models.CharField(max_length=100)
    start = models.IntegerField()
    stop = models.IntegerField()
    strand = models.CharField(max_length=10)
    length = models.IntegerField()
