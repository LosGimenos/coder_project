# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class Coder(models.Model):
    first_name = models.CharField(max_length=300, blank=True, null=True)
    middle_name = models.CharField(max_length=300, blank=True, null=True)
    last_name = models.CharField(max_length=300, blank=True, null=True)
    email = models.EmailField(blank=True, null=True, unique=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=10.0)
    username = models.CharField(max_length=300, blank=True, null=True)

class Project(models.Model):
    name = models.CharField(max_length=200)
    rate = models.DecimalField(max_digits=4, decimal_places=2)
    metadata = models.TextField(blank=True, null=True)
    contains_adverse_effects = models.BooleanField(default=False)
    coder = models.ManyToManyField(Coder)

class Column(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    column_name = models.TextField(null=True, blank=True, db_index=True)
    column_number = models.IntegerField(db_index=True, null=True)
    is_binary_variable = models.BooleanField(default=False)
    true_value = models.TextField(null=True, blank=True, db_index=True)
    false_value = models.TextField(null=True, blank=True, db_index=True)
    is_text_variable = models.BooleanField(default=False)
    is_number_variable = models.BooleanField(default=False)
    is_date_variable = models.BooleanField(default=False)
    is_variable = models.BooleanField(default=False)

    def __str__(self):
        return "Column = %s" % (self.column_name.__str__())
    class Meta:
        ordering = ['id']

class Variable(models.Model):
    name = models.CharField(blank=True, null=True, max_length=200)
    description = models.TextField(blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    is_freeform = models.BooleanField(default=False)
    is_multiple_choice = models.BooleanField(default=False)
    freeform_value = models.TextField(blank=True, null=True)
    multiple_choice_option_one = models.CharField(blank=True, null=True, max_length=2000)
    multiple_choice_option_two = models.CharField(blank=True, null=True, max_length=2000)
    multiple_choice_option_three = models.CharField(blank=True, null=True, max_length=2000)
    multiple_choice_option_four = models.CharField(blank=True, null=True, max_length=2000)
    multiple_choice_option_five = models.CharField(blank=True, null=True, max_length=2000)
    multiple_choice_option_six = models.CharField(blank=True, null=True, max_length=2000)
    multiple_choice_option_seven = models.CharField(blank=True, null=True, max_length=2000)
    column = models.ForeignKey(Column, on_delete=models.CASCADE, null=True)

class VariableLibrary(models.Model):
    name = models.CharField(null=True, max_length=200)
    description = models.TextField(blank=True, null=True)
    variable = models.ManyToManyField(Variable)

class RowStatus(models.Model):
    is_completed = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    coder = models.ForeignKey(Coder, on_delete=models.CASCADE, null=True)

class ProjectAdmin(models.Model):
    pass

class Tag(models.Model):
    name = models.CharField(null=True, max_length=200)
    variable = models.ManyToManyField(Variable)

class Group(models.Model):
    name = models.CharField(blank=True, null=True, max_length=200)
    description = models.TextField(blank=True, null=True)
    tag = models.ManyToManyField(Tag)

class Dataset(models.Model):
    dataset_ID = models.TextField(null=True, blank=True, db_index=True)
    show = models.BooleanField(default=True)
    path = models.TextField(null=True, blank=True)
    dataset_name = models.TextField(null=True, blank=True, db_index=True)
    created_date = models.DateTimeField(auto_now_add=True)
    id_column = models.IntegerField(null=True)
    date_column = models.IntegerField(null=True)
    def __str__(self):
        return "Dataset %s \n" % (self.dataset_ID.__str__())
    class Meta:
        ordering = ['id']

class Row(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    is_locked = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    coder = models.ForeignKey(Coder, null=True)
    row_name = models.TextField(null=True, blank=True, db_index=True)
    row_number = models.IntegerField(db_index=True, null=True)
    matches_filters = models.BooleanField(default=True)
    matches_category = models.BooleanField(default=True)
    matches_split = models.BooleanField(default=True)
    matches_split_exclusions = models.BooleanField(default=True)
    def __str__(self):
        return "Row = %s" % (self.row_name.__str__())

class Data(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)
    row = models.ForeignKey(Row, on_delete=models.CASCADE, null=True)
    column = models.ForeignKey(Column, on_delete=models.CASCADE, null=True)
    value = models.TextField(null=True, blank=True)
    date = models.DateTimeField(null=True)
    number = models.FloatField(null=True)
    def __str__(self):
        return "Row %s \n" % (self.row.__str__())
    class Meta:
        index_together = ('project', 'row', 'column')
