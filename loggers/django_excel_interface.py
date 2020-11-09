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
from django.db.utils import IntegrityError
import datetime
import pytz
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
    """Import score sheets exported from bondjango"""
    if request.method == "POST":
        # get the data from the upload form
        form = UploadFileForm(request.POST, request.FILES)
        # get the model's fields
        search_fields = ([f.name for f in ScoreSheet._meta.get_fields() if not f.is_relation])

        def mouse_namer(row):
            """Find the mouse instance in the database based on the mouse name"""
            q = Mouse.objects.filter(mouse_name=row[-2])[0]
            row[-2] = q
            p = User.objects.filter(username=row[-1])[0]
            row[-1] = p
            return row

        # check that the form is valid
        if form.is_valid():

            # split the book into sheets and pass one at a time, since the mouse names are in the mouse sheets and
            # django excel expects the model name to be the sheet name
            full_book = request.FILES['file'].get_book_dict()
            # for all the sheets
            for single_sheet in full_book:
                # load the sheet to check for contents
                target_sheet = full_book[single_sheet]
                print(target_sheet)
                # if it's empty, skip
                if target_sheet[0][0] == '':
                    continue
                try:
                    # save to the database
                    request.FILES['file'].save_to_database(model=ScoreSheet, initializer=mouse_namer,
                                                           mapdict=search_fields + ['mouse', 'owner'],
                                                           sheet_name=single_sheet)
                except IntegrityError:
                    # if the entry is already there, give a warning and skip
                    print('entry for mouse %s already in database' % single_sheet)

            # TODO: use the other response where I only display the sheet being uploaded
            return HttpResponse(embedhandson_table(request))
        else:
            return HttpResponseBadRequest()
    else:
        form = UploadFileForm()
    return render(request, 'upload_form.html', {'form': form, 'title': 'Import', 'header': 'Upload data'})


def import_old_data(request):
    """Import a score sheet spreadsheet saved manually (i.e. old ones)"""
    if request.method == "POST":
        # get the data from the upload form
        form = UploadFileForm(request.POST, request.FILES)

        # check that the form is valid
        if form.is_valid():

            # split the book into sheets and pass one at a time, since the mouse names are in the mouse sheets and
            # django excel expects the model name to be the sheet name
            full_book = request.FILES['file'].get_book_dict()
            # for all the sheets
            for mouse_name in full_book:
                # get the sheet
                single_sheet = full_book[mouse_name]
                # for all the entries in the single sheet
                for entry_raw in single_sheet[1:]:
                    # if the date value is absent, skip
                    if entry_raw[0] == '':
                        continue
                    # eliminate empty spaces
                    entry = [0 if el in [''] else el for el in entry_raw]
                    # eliminate N/A and A/L
                    entry = [1 if el in ['N/A', 'A/L', 'AL'] else el for el in entry]
                    # get the mouse instance
                    mouse_instance = Mouse.objects.get(mouse_name=mouse_name)

                    # get the owner
                    owner_instance = mouse_instance.owner

                    # format the date
                    date = datetime.datetime.strptime(entry[0], '%d.%m.%y')
                    date = date.replace(tzinfo=pytz.UTC)
                    # create a string formatted as a slug to search for repeated ones
                    # print(date.strftime('%Y-%m-%d-%H%M%S'))
                    # print(len(ScoreSheet.objects.filter(slug=date.strftime('%Y-%m-%d-%H%M%S'))))
                    while len(ScoreSheet.objects.filter(slug=date.strftime('%Y-%m-%d-%H%M%S'))) > 0:
                        date += datetime.timedelta(minutes=20)

                    # assemble the dictionary for creating the entries
                    data_dict = {
                        'sheet_date': date,
                        'carprofen': 1 if entry[1] == 'x' else 0,
                        'weight': float(entry[2]),
                        'food_consumed': float(entry[3]),
                        'behavior': float(entry[4]),
                        'posture_fur': float(entry[5]),
                        'water_food_uptake': float(entry[6]),
                        'general_condition': float(entry[7]),
                        'skin_turgor': float(entry[8]),
                        'brain_surgery': float(entry[9]),
                        'notes': '' if len(entry) == 11 else entry[11],
                        'mouse': mouse_instance,
                        'owner': owner_instance,
                    }
                    # create the model instance with the data
                    model_instance = ScoreSheet.objects.create(**data_dict)
                    # save the model instance
                    # model_instance.save()

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
    out_book.save_as(book_path)

    # the following code prompts the user to save the spreadsheet wherever, might be useful later
    # book_stream = sources.save_book(out_book, file_type='xls')
    # # get the response
    # response = excel._make_response(book_stream, 'xls', 200, file_name=file_name)
    # # get the content disposition from the response to add to the http response
    # content_disposition = {'Content-Disposition': response['Content-Disposition']}
    # # get the http response
    # hresponse = HttpResponse(response, content_type='application/vnd.ms-excel')
    # # edit the headers to include the content disposition, since for some reason httpresponse doesn't do it
    # hresponse._headers['content-disposition'] = list(content_disposition.items())[0]
    # return hresponse
    return HttpResponseRedirect('/loggers/score_sheet/')


def weights_function(request, data, fields):
    """Plot the weight and the consumed food for a given animal over time"""
    # get the sheet
    sheet = excel.pe.get_sheet(query_sets=data, column_names=fields)
    # name the columns of the sheet by the first row (since pyexcel is agnostic to this unless pointed out)
    sheet.name_columns_by_row(0)
    # format the dates for labeling
    dates = [el[:10] for el in sheet.column['sheet_date']]
    # define the data dictionary
    data_dict = {
        'Date': sheet.column['sheet_date'],
        'Food': sheet.column['food_consumed'],
        'Weight': sheet.column['weight'],
    }

    # print(sheet.name_rows_by_column())
    svg = excel.pe.save_as(
        adict=data_dict,
        dest_label_x_in_column=0,
        dest_x_labels=dates,
        dest_file_type='svg',
        dest_chart_type='line',
        dest_title='Weight progression',
        dest_width=1600,
        dest_height=800
    )

    return render(request, 'weight_chart.html', dict(svg=svg.read()))


def percentage_function(request, data, fields, restrictions):
    """Plot the percentage weight for an animal during restriction"""
    # get the start date
    start_date = str(restrictions[0].start_date)[:10]
    print(start_date)
    # get the sheet
    sheet = excel.pe.get_sheet(query_sets=data, column_names=fields)
    # name the columns of the sheet by the first row (since pyexcel is agnostic to this unless pointed out)
    sheet.name_columns_by_row(0)
    # format the dates for labeling
    dates = [el[:10] for el in sheet.column['sheet_date']]
    # get the index of the start date
    idx_start = dates.index(start_date)
    # calculate percentage weight
    percentage_weight = [el*100/sheet.column['weight'][idx_start] for el in sheet.column['weight'][idx_start:]]
    # rewrite dates also for plotting
    plot_dates = dates[idx_start:]
    print(plot_dates)
    # define the data dictionary
    data_dict = {
        'Date': plot_dates,
        'Percentage': percentage_weight,
    }

    # print(sheet.name_rows_by_column())
    svg = excel.pe.save_as(
        adict=data_dict,
        dest_label_x_in_column=0,
        dest_x_labels=plot_dates,
        dest_file_type='svg',
        dest_chart_type='line',
        dest_title='Weight progression',
        dest_width=1600,
        dest_height=800
    )

    return render(request, 'weight_chart.html', dict(svg=svg.read()))
