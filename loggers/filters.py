from rest_framework import filters


class DynamicSearchFilter(filters.SearchFilter):

    # def get_search_fields(self, view, request):
    #     print(request.GET)
    #     print('yay')
    #     return request.GET.getlist('search_fields', [])

    def split_terms_fields(self, request):

        # search_full = self.get_search_terms(request)
        search_full = request.query_params.get(self.search_param, '')
        search_full = search_full.replace(',', ' ').split()

        search_terms = []
        search_fields = []

        for el in search_full:
            separated = el.replace('=', ' ').split()
            search_fields.append(separated[0])
            search_terms.append(separated[1])

        return search_terms, search_fields

    def get_search_terms(self, request):

        return self.split_terms_fields(request)[0]

    def filter_queryset(self, request, queryset, view):

        # get the original search fields
        original_search_fields = getattr(view, 'search_fields', None)

        _, search_fields = self.split_terms_fields(request)

        # search_fields = ['lighting']
        setattr(view, 'search_fields', search_fields)
        queryset = super().filter_queryset(request, queryset, view)

        setattr(view, 'search_fields', original_search_fields)

        return queryset
