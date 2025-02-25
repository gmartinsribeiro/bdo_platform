# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from decimal import Decimal
from query_designer.api import *
from query_designer.lists import AGGREGATES
from query_designer.query import *
import json
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.conf import settings
from visualizer.models import Visualization
from datetime import datetime, timedelta
import time

def index(request):
    return render(request, 'query_designer/index.html', {
        'sidebar_active': 'queries',
    })


def load_query(request, pk):
    q = Query.objects.get(pk=pk)

    return JsonResponse({
        'pk': q.pk,
        'title': q.title,
        'design': q.design,
        'document': q.document
    })


def simplified(request, pk=None):
    storage_target = settings.STORAGE_TARGET
    public_datasets = Dataset.objects.filter(stored_at=storage_target, private=False).exclude(variables=None)
    user_datasets = Dataset.objects.filter(stored_at=storage_target, owner=request.user, private=True).exclude(variables=None)

    user_with_access_datasets_list = []
    if request.user.is_authenticated():
        for access in DatasetAccess.objects.filter(user=request.user, valid=True):
            s = access.start
            e = access.end
            if datetime(s.year, s.month, s.day) < datetime.now() < datetime(e.year, e.month, e.day):
                user_with_access_datasets_list.append(access.dataset.id)

    user_with_access_datasets = Dataset.objects.filter(id__in=user_with_access_datasets_list)

    # combine user and public datasets to show to the user
    user_datasets = user_datasets | public_datasets
    dataset_list = public_datasets | user_datasets | user_with_access_datasets
    organization_list = Organization.objects.all()
    variable_list = Variable.objects.all()


    return render(request, 'query_designer/simplified.html', {
        'organizations' : organization_list,
        'variables' : variable_list,
        'datasets': dataset_list,
        'dimensions': Dimension.objects.all(),
        'temp_queries_count': TempQuery.objects.last().id,
        'available_viz': Visualization.objects.filter(hidden=False).order_by('id'),
        'AGGREGATES': AGGREGATES,
    })


def clean(request, pk=None):
    storage_target = settings.STORAGE_TARGET
    public_datasets = Dataset.objects.filter(stored_at=storage_target, private=False).exclude(variables=None)
    user_datasets = Dataset.objects.filter(stored_at=storage_target, owner=request.user, private=True).exclude(variables=None)

    user_with_access_datasets_list = []
    if request.user.is_authenticated():
        for access in DatasetAccess.objects.filter(user=request.user, valid=True):
            s = access.start
            e = access.end
            if datetime(s.year, s.month, s.day) < datetime.now() < datetime(e.year, e.month, e.day):
                user_with_access_datasets_list.append(access.dataset.id)

    user_with_access_datasets = Dataset.objects.filter(id__in=user_with_access_datasets_list, stored_at=storage_target)

    # combine user and public datasets to show to the user
    user_datasets = user_datasets | public_datasets
    dataset_list = public_datasets | user_datasets | user_with_access_datasets
    # dataset_list.order_by('order')
    publisher_list = sorted(set([d.publisher for d in dataset_list]))
    organization_list = sorted(set([d.publisher for d in dataset_list]))
    observation_list = sorted(set([d.observations for d in dataset_list]))
    license_list = sorted(set([d.license for d in dataset_list]))
    # for dataset in dataset_list:
    #     if dataset.organization.title not in organization_list:
    #         organization_list.append(dataset.organization.title)
    variable_list = Variable.objects.all().order_by('title')
    variable_list_filter = sorted(set([(v.safe_name, v.title) for v in variable_list]))

    time_start_timestamp = min([d.temporalCoverageBeginTimestamp for d in Dataset.objects.all() if d.temporalCoverageBeginTimestamp != ""])
    date_now = datetime.now()
    time_end_timestamp = max([d.temporalCoverageEndTimestamp for d in Dataset.objects.all() if d.temporalCoverageEndTimestamp != ""] + [long(time.mktime(date_now.timetuple())) * 1000])

    try:
        with open('visualizer/static/visualizer/visualisations_settings.json') as f:
            conf_viz_json = json.dumps(json.load(f))
    except:
        pass
    return render(request, 'query_designer/clean.html', {
        'organizations': organization_list,
        'publishers': publisher_list,
        'observations': observation_list,
        'licenses': license_list,
        'variables': variable_list,
        'variable_list_filter': variable_list_filter,
        'datasets': dataset_list.order_by('order'),
        'dimensions': Dimension.objects.all(),
        # 'query': TempQuery.objects.filter(user=request.user).latest('created'), #last temporary query of this particular user
        'available_viz': Visualization.objects.filter(hidden=False).order_by('order'),
        'AGGREGATES': AGGREGATES,
        'visualisation_configuration': conf_viz_json,
        'time_start_timestamp': time_start_timestamp,
        'time_end_timestamp': time_end_timestamp,
    })


@csrf_exempt
def save_query(request, pk=None, temp=1):
    print pk, temp
    # create or update
    if not pk:
        current_user = request.user
        if current_user.is_authenticated():
            if int(temp) == 1:
                print 'it is temp'
                q = TempQuery(user=current_user)
            else:
                q = Query(user=current_user)
        else:
            if int(temp) == 1:
                q = TempQuery(user=User.objects.get(username='BigDataOcean'))
            else:
                q = Query(user=User.objects.get(username='BigDataOcean'))
    else:
        print 'not pk'
        q = AbstractQuery.objects.get(pk=pk)

    # initially assume custom query
    q.generated_by = 'CUSTOM'

    # document
    if 'document' in request.POST:
        try:
            doc = json.loads(request.POST.get('document', ''))
        except ValueError:
            return JsonResponse({'error': 'Invalid query document'}, status=400)

        q.document = doc

    # design
    if 'design' in request.POST:
        try:
            design = json.loads(request.POST.get('design', ''))
        except ValueError:
            return JsonResponse({'error': 'Invalid design'}, status=400)

        q.design = design
        q.generated_by = 'QDv1'
    else:
        q.design = None

    # v2 fields
    v2_fields = request.POST.get('v2_fields', '')
    v2_filters = request.POST.get('v2_options', '')
    if v2_fields:
        q.v2_fields = json.dumps(json.loads(v2_fields))
        q.generated_by = 'QDv2'

        if v2_filters:
            q.v2_filters = v2_filters

    # title
    if 'title' in request.POST:
        q.title = request.POST.get('title', 'Untitled query')

    # save
    q.save()

    # return OK response
    return JsonResponse({
        'pk': q.pk,
        'title': q.title,
    })


def get_query_variables(request):
    if 'id' in request.GET:
        id = int(request.GET.get('id'))
        doc = None
        # existing saved query
        if id >= 0:
            # get the query
            q = AbstractQuery.objects.get(pk=id)
            # get the document
            doc = q.document
        # new query
        else:
            if 'document' in request.GET:
                try:
                    doc = json.loads(request.GET.get('document', ''))
                except ValueError:
                    return JsonResponse({'error': 'Invalid query document'}, status=400)

        # find the query's SELECT variables formatted as: 'variable's column name (title)': 'variable's name'
        variables = dict()
        dimensions = dict()
        for from_clause in doc['from']:
            for col in from_clause['select']:
                if col['type'] == 'VALUE':
                    variables[col['title']] = col['name']
                else:
                    dimensions[col['title']] = col['name']

        result = {'variables': variables, 'dimensions': dimensions}
        # return the found variables
        return HttpResponse(json.dumps(result), content_type="application/json")

    else:
        return JsonResponse({'error': 'Invalid query document'}, status=400)


class DefaultEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        elif isinstance(o, datetime.datetime):
            return o.isoformat()
        elif isinstance(o, datetime.date):
            return o.isoformat()

        return super(DefaultEncoder, self).default(o)


def filter_info(request, filter_type, pk):
    if filter_type == 'variable':
        return JsonResponse({'type': 'text'})
        # return JsonResponse({'type': 'number', 'orderable': True})

    dimension = Dimension.objects.get(pk=pk)

    # values = dimension.ranges
    # TODO: change this, get proper dimension ranges
    values = {
        'type': 'text'
    }
    return JsonResponse(values, encoder=DefaultEncoder)

    if type(values) == dict and 'min' in values:
        values.update({
            'type': 'text',
            'orderable': True,
        })

        return JsonResponse(values, encoder=DefaultEncoder)

    return JsonResponse({
        'type': 'select',
        'orderable': True,
        'options': [{
            'name': v,
            'value': v,
        } for v in values]
    }, encoder=DefaultEncoder)


def load_to_analysis(request):
    current_user = request.user
    if current_user.is_authenticated():
        q = Query(user=current_user)
    else:
        q = Query(user=User.objects.get(username='BigDataOcean'))

    # document
    if 'document' in request.GET:
        try:
            doc = json.loads(request.GET.get('document', ''))
        except ValueError:
            return JsonResponse({'error': 'Invalid query document'}, status=400)

        q.document = doc

    # title
    if 'title' in request.GET:
        q.title = request.GET.get('title', 'Untitled query')

    # return OK response
    return JsonResponse({
        'raw_query': q.raw_query,
        'title': q.title,
    })


def get_field_policy(user):
    field_policy = {
        'categories': [],
        'variables': [],
        'aggregates': [],
    }

    # for variable in Variable.objects.all():
    #     field_policy['variables'].append({
    #         'name': variable.safe_name,
    #         'title': variable.title,
    #         'id': variable.pk,
    #         'description': variable.description,
    #         'dataType': variable.dataType,
    #     })

    for aggregate in AGGREGATES:
        field_policy['aggregates'].append({
            'title': aggregate[1],
            'value': aggregate[0],
            'typelist': aggregate[2],
        })

    return field_policy


def get_config(request):
    return JsonResponse(get_field_policy(request.user if request.user.is_authenticated else None))


def list_queries(request):
    user = request.user if request.user.is_authenticated() else None

    # ensure GET request
    if request.method != 'GET':
        return HttpResponse('Only `GET` method allowed', status=400)

    ctx = {
        'queries': Query.objects.filter(user=user, generated_by='CUSTOM').order_by().order_by('-created', '-updated'),
    }

    return render(request, 'query_designer/utils/query-table.html', ctx)


def delete_query(request, pk):
    # ensure POST request
    if request.method != 'POST':
        return HttpResponse('Only `POST` method allowed', status=400)

    try:
        query = AbstractQuery.objects.get(pk=int(pk), user=request.user)
        query.delete()
        return HttpResponse('', status=204)
    except Query.DoesNotExist as e:
        return HttpResponse('Query not found', status=404)


def open_chart(request, pk):
    user = request.user if request.user.is_authenticated() else None

    # ensure GET request
    if request.method != 'GET':
        return HttpResponse('Only `GET` method allowed', status=400)

    # check if chart exists & is owned by this user
    try:
        chart = Query.objects.filter(user=user).get(pk=pk)
    except Query.DoesNotExist as e:
        return HttpResponse('Query not found', status=404)

    # return the chart info
    return JsonResponse({
        'title': chart.title,
        'chartOptions': json.loads(chart.v2_fields),
        'chartFilters': chart.v2_filters,
        'chartPolicy': get_field_policy(user=user),
    }, safe=True, encoder=DefaultEncoder)


def save_formulas(request):
    user = request.user if request.user.is_authenticated() else None

    # ensure POST request
    if request.method != 'POST':
        return HttpResponse('Only `POST` method allowed', status=400)

    try:
        formulas = json.loads(request.POST.get('formulas'))
    except ValueError:
        return HttpResponse('Invalid formula input', status=400)

    # list with formulas to remove -- assume all
    to_delete_ids = [f.pk for f in Formula.objects.filter(created_by=user)]

    result = []
    with transaction.atomic():
        for formula in formulas:

            if not formula.get('formulaName') or not formula.get('formulaValue'):
                return HttpResponse('`formula_name` and `formula_value` are both required for a formula', status=400)

            # save the formula
            try:
                if not formula['formulaId']:
                    raise Formula.DoesNotExist()

                fo = Formula.objects.get(pk=formula['formulaId'])
            except Formula.DoesNotExist:
                fo = Formula.objects.create(name=formula['formulaName'], created_by=user)

            fo.value = formula['formulaValue']
            fo.name = formula['formulaName']
            fo.save()

            # remove from to_delete list
            if fo.pk in to_delete_ids:
                to_delete_ids.pop(to_delete_ids.index(fo.pk))

            # validate formula
            result.append({
                'name': fo.name,
                'id': fo.pk,
                'errors': fo.errors(),
                'unit': fo.unit,
            })

    # delete any formula not submitted
    Formula.objects.filter(pk__in=to_delete_ids, created_by=user).delete()

    # respond
    return JsonResponse(result, safe=False)


def delete_formula(request):
    # ensure POST request
    if request.method != 'POST':
        return HttpResponse('Only `POST` method allowed', status=400)

    # get the formula info
    formula_name = request.POST.get('formula_name', '')

    try:
        formula = Formula.objects.get(name=formula_name, created_by=request.user if request.user.is_authenticated() else None)
    except Formula.DoesNotExist as e:
        return HttpResponse('Formula "%s" not found' % formula_name, status=404)

    # delete & send OK response
    formula.delete()
    return HttpResponse('', status=204)


def formulas(request):
    template = 'query_designer/utils/formula-editor.html'

    if request.is_ajax():
        template = 'query_designer/utils/formula-editor-content.html'
    return render(request, template, {
        'formulas': Formula.objects.filter(created_by=request.user if request.user.is_authenticated() else None).order_by('date_created'),
        'value_properties': [(v.name, v.title) for v in Variable.objects.all()] + [(d.name, d.title) for d in Dimension.objects.all()],
        'formula_functions': Formula.safe_function_info(),
    })


def new_template(request):
    return render(request, 'query_designer/new_template.html', {})
