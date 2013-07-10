## -*- coding: utf-8 -*-


## Weckan -- Web application using CKAN model
## By: Emmanuel Raviart <emmanuel@raviart.com>
##
## Copyright (C) 2013 Emmanuel Raviart
## http://gitorious.org/etalab/weckan
##
## This file is part of Weckan.
##
## Weckan is free software; you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Weckan is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.


<%!
import collections

from weckan import urls
from weckan.model import meta, Package
%>


<%inherit file="site.mako"/>


<%def name="breadcrumb()" filter="trim">
</%def>


<%def name="container_content()" filter="trim">
##        <div class="page-header">
##            <h1><%self:brand/></h1>
##        </div>
        <%self:hero_unit/>
        <div>
            <ul>
    % for package in meta.Session.query(Package).limit(10):
                <li><a href="${package.get_url(ctx)}">${package.title}</a></li>
    % endfor
            </ul>
        </div>
</%def>


<%def name="hero_unit()" filter="trim">
##<%
##    user = model.get_user(ctx)
##%>
        <div class="hero-unit">
            <h2>${_(u"Welcome to Weckan")}</h2>
            <p>${_(u"A safe and easy way to publish forms")}</p>
##    % if user is None:
            <a class="btn btn-large btn-primary" href="${urls.get_url(ctx, 'login')}">${_('Sign In')}</a>
##    % endif
        </div>
</%def>
