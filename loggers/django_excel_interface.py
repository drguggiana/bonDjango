import django_excel as excel
from django.shortcuts import render, redirect
from .models import ScoreSheet, Mouse, User, MouseSet
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django import forms
from .serializers import slugify
import pyexcel as pe
import pyexcel.constants as constants
import pyexcel.internal.core as sources
from pyexcel.core import _split_keywords
from pyexcel.sheet import Sheet
import os


class UploadFileForm(forms.Form):
    file = forms.FileField()


def handson_table(request, query_sets, fields):
    """function to render the scoresheets as part of the template"""
    return excel.make_response_from_query_sets(query_sets, fields, 'handsontable.html')

    # content = excel.pe.save_as(source=query_sets,
    #                            dest_file_type='handsontable.html',
    #                            dest_embed=True)
    # content.seek(0)
    # return render(
    #     request,
    #     'custom-handson-table.html',
    #     {
    #         'handsontable_content': content.read()
    #     })
    # return Response({'handsontable_content': render(content)}, template_name='custom-handson-table.html')


def embedhandson_table(request):
    content = excel.pe.save_as(
        model=ScoreSheet,
        dest_file_type='handsontable.html',
        dest_embed=True)
    content.seek(0)

    return render(
        request,
        'custom-handson-table.html',
        {
            'handsontable_content': content.read()
        })


def import_data(request):

    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        search_fields = ([f.name for f in ScoreSheet._meta.get_fields() if not f.is_relation])

        def na_remover(row):
            row = [0 if el == 'N/A' else el for el in row]
            return row

        def mouse_namer(row):
            q = Mouse.objects.filter(mouse_name=row[-2])[0]
            row[-2] = q
            p = User.objects.filter(username=row[-1])[0]
            row[-1] = p
            return row

        def fix_format(row):
            # read the different sheets
            slug_field = slugify(str(row[1])[0:19])
            return row
        if form.is_valid():
            print(request.FILES['file'])

            def save_book_as(**keywords):
                return
            request.FILES['file'].save_book_to_database(models=[ScoreSheet], initializers=[mouse_namer],
                                                        mapdicts=[search_fields+['mouse', 'owner']])
                                                        # mapdicts=[search_fields.sort()])
            return HttpResponse(embedhandson_table(request))
        else:
            return HttpResponseBadRequest()
    else:
        form = UploadFileForm()
    return render(request, 'upload_form.html', {'form': form, 'title': 'Import', 'header': 'Upload data'})


def export_data(request, atype, queryset, fields):
    if atype == "sheet":
        return excel.make_response_from_a_table(ScoreSheet, 'xls', file_name="sheet")
    elif atype == "book":
        return excel.make_response_from_tables([ScoreSheet], 'xls', file_name="book")
    elif atype == "custom":
        return excel.make_response_from_query_sets(queryset, fields, 'xls', file_name='custom')
    else:
        return HttpResponseBadRequest("bad request, choose one")


def export_network(instance, request):
    # get the license from this animal
    license_object = instance.get_object().mouse.mouse_set.license
    # get the user from this animal
    user_object = license_object.owner
    # get all the mice from this license and user
    # first get the mouse_sets
    mouse_sets = MouseSet.objects.filter(owner=user_object, license=license_object)
    # now get the mice within this mouse set
    mice = [list(el.mouse.all()) for el in mouse_sets]
    # flatten the list
    mice = [el for sublist in mice for el in sublist]
    # get the corresponding scoresheets
    scoresheets = [list(el.score_sheet.all()) for el in mice]
    # get the fields
    # get the fields
    fields = ([f.name for f in ScoreSheet._meta.get_fields() if not f.is_relation] + ['mouse__mouse_name',
                                                                                      'owner__username'])
    # allocate a dictionary to store the scoresheets
    out_dict = {}

    # for all the mice
    for idx, animal in enumerate(scoresheets):
        # generate the name of the sheet
        sheet_name = str(mice[idx])

        dest_keywords, source_keywords = _split_keywords(query_sets=animal, column_names=fields,
                                                         dest_file_type='xls')
        sheet_params = {}
        for field in constants.VALID_SHEET_PARAMETERS:
            if field in source_keywords:
                sheet_params[field] = source_keywords.pop(field)
        sheet_stream = sources.get_sheet_stream(**source_keywords)
        # turn it into a sheet
        sheet = Sheet(sheet_stream.payload, sheet_name, **sheet_params)
        # put in the dictionary
        out_dict[sheet_name] = sheet

    # turn the dictionary into a book
    out_book = pe.get_book(bookdict=out_dict)

    # get the file name for the book
    file_name = ' '.join(('Score Sheet', license_object.license_id.split('_')[1], 'Food Water', str(user_object))) \
                + '.xls'
    # get the final path
    book_path = os.path.join(license_object.score_sheet_path, file_name)
    # save the book to file
    book_stream = sources.save_book(out_book, file_type='xls')
    # print(excel._make_response(book_stream, 'xls', 200, book_path).__dict__)
    # file_stream = pe.save_as(query_sets=scoresheets[0], column_names=fields,
    #                          dest_file_type='xls')
    # sheet = file_stream.sheet

    # print(file_stream.read())
    return HttpResponse(excel._make_response(book_stream, 'xls', 200, book_path), content_type='application/msexcel')
    # return HttpResponse(export_data(request, "custom", scoresheets[0], fields), content_type='application/msexcel')
    # return HttpResponseRedirect('/loggers/score_sheet/')

