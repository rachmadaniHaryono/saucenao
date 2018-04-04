import os
import hashlib

from tempfile import NamedTemporaryFile
from flask import request, url_for, abort
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import BaseSQLAFilter
from jinja2 import Markup
import vcr

from . import forms, saucenao, models


def md5_checksum(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def sha256_checksum(filename, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            sha256.update(block)
    return sha256.hexdigest()


class HomeView(AdminIndexView):
    @expose('/', methods=('GET', 'POST'))
    def index(self):
        index_form = forms.IndexForm()
        kwargs = {}
        if request.method == 'POST':
            with NamedTemporaryFile() as f:
                file_data = index_form.upload.data
                ext = os.path.split(file_data.filename)[0]
                # filename = f.name + ext
                filename = 'temp.jpg'
                file_data.save(filename)
                output_type = int(index_form.output_type.data)
                combine_api_types = index_form.combine_api_types.data
                sn = saucenao.SauceNao(
                    '', minimum_similarity=0,
                    combine_api_types=combine_api_types,
                    output_type=int(output_type),
                )
                session = models.db.session
                c_sha256, c_sha256_created = models.get_or_create(
                    session, models.Checksum,
                    value=sha256_checksum(filename),
                    type=models.Checksum.TYPE_SHA256
                )
                c_md5 = models.get_or_create(
                    session, models.Checksum,
                    value=md5_checksum(filename),
                    type=models.Checksum.TYPE_MD5
                )[0]
                if c_sha256_created:
                    with vcr.use_cassette('vcr_cassettes/index.yaml'):
                        res = sn.check_file(filename)
                        if not res:
                            abort(404)
                        search_m = models.Search(output_type=output_type, checksums=[c_sha256, c_md5], combine_api_types=combine_api_types)
                        for item in res:
                            title, title_created = models.get_or_create(session, models.Title, value=item['data']['title'])
                            if title_created:
                                result_m = models.get_or_create(session, models.Result, title=title)[0]
                                for item in res:
                                    for data_content in item['data']['content']:
                                        data_content = data_content.strip()
                                        if data_content:
                                            content_m = models.get_or_create(session, models.Content, value=data_content)[0]
                                            if ':' in data_content:
                                                namespace, tag_value = data_content.split(':', 1)
                                                namespace_m = models.get_or_create(session, models.Namespace, value=namespace)[0]
                                                tag_m = models.get_or_create(session, models.Tag, value=tag_value, namespace=namespace_m)[0]
                                                content_m.tags.append(tag_m)
                                            result_m.contents.append(content_m)
                                    for url in item['data']['ext_urls']:
                                        url_m = models.get_or_create(session, models.Url, value=url)[0]
                                        result_m.external_urls.append(url_m)
                                    result_m.similarity = float(item['header']['similarity'])
                                search_m.results.append(result_m)
                            else:
                                # TODO
                                results_from_title = title.results
                        session.add(search_m)
                        session.commit()
                        kwargs['entry'] = search_m
                else:
                    # TODO
                    searchs = c_sha256.searchs
                    kwargs['entry'] = searchs[0]
        return self.render('saucenao/index.html', index_form=index_form, **kwargs)
