from rest_framework import filters


class DynamicSearchFilter(filters.SearchFilter):

    # def get_search_fields(self, view, request):
    #     print(request.GET)
    #     print('yay')
    #     return request.GET.getlist('search_fields', [])

    def split_terms_fields(self, request):

        # get the search parameters
        search_full = request.query_params.get(self.search_param, '')
        # split the different parts of the query
        search_full = search_full.replace(',', ' ').split()
        # allocate memory for the terms and fields
        search_terms = []
        search_fields = []
        # for all the terms
        for el in search_full:
            # if = is not there, assume the search term (and not the field) was given
            if ':' not in el:
                search_terms.append(el)
            else:
                # otherwise, split the query and save the term and field
                separated = el.replace(':', ' ').split()
                search_fields.append(separated[0])
                # check if space was added as a query
                if len(separated) == 1:
                    search_terms.append('')
                else:
                    search_terms.append(separated[1])

        return search_terms, search_fields

    def get_search_terms(self, request):

        return self.split_terms_fields(request)[0]

    def filter_queryset(self, request, queryset, view):
        # TODO: figure out a way of checking for empty fields
        # get the original search fields
        original_search_fields = getattr(view, 'search_fields', None)
        # get the user specified search terms
        _, search_fields = self.split_terms_fields(request)

        # if no search terms were used, just use the originals
        if len(search_fields) == 0:
            search_fields = original_search_fields
        setattr(view, 'search_fields', search_fields)

        queryset = super().filter_queryset(request, queryset, view)

        setattr(view, 'search_fields', original_search_fields)

        return queryset
