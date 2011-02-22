# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from collections import defaultdict

from django.http import Http404

from feincms import settings
from feincms.content.application.models import ApplicationContent
from feincms.module.page.models import Page
from feincms.views.base import Handler

try:
    any
except NameError:
    # For Python 2.4
    from feincms.compat import c_any as any



class ApplicationContentHandler(Handler):
    def __call__(self, request, path=None):
        return self.build_response(request,
            Page.objects.best_match_for_path(path or request.path))

    def prepare(self, request, page):
        # Used to provide additional app-specific context variables:
        if not hasattr(request, '_feincms_appcontent_parameters'):
            request._feincms_appcontent_parameters = dict(in_appcontent_subpage=False)

        has_appcontent = page_has_appcontent(page)

        if request.path != page.get_absolute_url():
            # The best_match logic kicked in. See if we have at least one
            # application content for this page, and raise a 404 otherwise.
            if not has_appcontent:
                if not settings.FEINCMS_ALLOW_EXTRA_PATH:
                    raise Http404
            else:
                request._feincms_appcontent_parameters['in_appcontent_subpage'] = True

            extra_path = request.path[len(page.get_absolute_url()):]
            extra = extra_path.strip('/').split('/')
            request._feincms_appcontent_parameters['page_extra_path'] = extra
            request.extra_path = extra_path
        else:
            request.extra_path = ""

        response = page.setup_request(request)
        if response:
            return response

        if has_appcontent:
            for content in page.content.all_of_type(ApplicationContent):
                r = content.process(request)
                if r and (r.status_code != 200 or request.is_ajax() or getattr(r, 'standalone', False)):
                    return r

    def finalize(self, request, response, page):
        _update_response_headers(request, page_has_appcontent(page), response)
        return super(ApplicationContentHandler, self).finalize(request, response, page)

#handler = ApplicationContentHandler()


class NewApplicationContentHandler(Handler):
    def __call__(self, request, path=None):
        request._feincms_appcontent_parameters = {}

        return self.build_response(request,
            Page.objects.best_match_for_path(path or request.path, raise404=True))

handler = NewApplicationContentHandler()



def page_has_appcontent(page):
    return any(page.content.all_of_type(ApplicationContent))
