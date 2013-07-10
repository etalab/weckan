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


<%doc>
    Site template inherited by each page
</%doc>


<%!
import urlparse

from weckan import conf, model, urls
%>


<%def name="body_content()" filter="trim">
    <div class="container-fluid"><div class="row-fluid">
        <%self:breadcrumb/>
        <%self:container_content/>
        <%self:footer/>
    </div></div>
</%def>


<%def name="brand()" filter="trim">
${conf['realm']}
</%def>


<%def name="breadcrumb()" filter="trim">
        <ul class="breadcrumb">
            <%self:breadcrumb_content/>
        </ul>
</%def>


<%def name="breadcrumb_content()" filter="trim">
            <li><a href="${urls.get_url(ctx)}">${_('Home')}</a> <span class="divider">/</span></li>
</%def>


<%def name="container_content()" filter="trim">
</%def>


<%def name="css()" filter="trim">
    <%self:css_bootstrap/>
    <link rel="stylesheet" href="/css/site.css">
    ## Bootstrap responsive CSS must be after site CSS.
    <link rel="stylesheet" href="${urlparse.urljoin(conf['bootstrap'], 'css/bootstrap-responsive.min.css')}">
</%def>


<%def name="css_bootstrap()" filter="trim">
    <link rel="stylesheet" href="${urlparse.urljoin(conf['bootstrap'], 'css/bootstrap.min.css')}">
</%def>


<%def name="error_alert()" filter="trim">
    % if errors:
                <div class="alert alert-block alert-error">
                    <h4 class="alert-heading">${_('Error!')}</h4>
        % if '' in errors:
<%
            error = unicode(errors[''])
%>\
            % if u'\n' in error:
                    <pre class="break-word">${error}</error>
            % else:
                    ${error}
            % endif
        % else:
                    ${_(u"Please, correct the informations below.")}
        % endif
                </div>
    % endif
</%def>


<%def name="feeds()" filter="trim">
</%def>


<%def name="footer()" filter="trim">
        <footer class="footer">
            <%self:footer_service/>
            <p>
                ${_('{0}:').format(_('Software'))}
                <a href="http://gitorious.org/etalab/weckan" rel="external">Weckan</a>
                &mdash;
                <span>Copyright © 2013 Emmanuel Raviart</span>
                &mdash;
                <a href="http://www.gnu.org/licenses/agpl.html" rel="external">${_(
                    'GNU Affero General Public License')}</a>
            </p>
        </footer>
</%def>


<%def name="footer_service()" filter="trim">
</%def>


<%def name="hidden_fields()" filter="trim">
</%def>


<%def name="metas()" filter="trim">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</%def>


<%def name="scripts()" filter="trim">
    <script src="${conf['jquery.js']}"></script>
    <%self:scripts_bootstrap/>
    <script>
function poptastic(url) {
    var newWindow = window.open(url, '_blank');
    if (window.focus) {
        newWindow.focus();
    }
}


$(function () {
    $('.dropdown-toggle').dropdown();
});
    </script>
</%def>


<%def name="scripts_bootstrap()" filter="trim">
    <script src="${urlparse.urljoin(conf['bootstrap'], 'js/bootstrap.min.js')}"></script>
</%def>


<%def name="title_content()" filter="trim">
<%self:brand/>
</%def>


<%def name="topbar()" filter="trim">
    <div class="navbar navbar-fixed-top">
        <div class="navbar-inner">
            <div class="container-fluid">
                ## .btn-navbar is used as the toggle for collapsed navbar content.
                <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                </a>
                <a class="brand" href="/"><%self:brand/> <span class="label label-warning">pre-alpha</span></a>
                <div class="nav-collapse">
                    <ul class="nav">
                        <%self:topbar_dropdown_admin/>
##                        <li><a href="${model.Project.get_class_url(ctx)}">${_('Forms')}</a></li>
##                        <li><a href="${urls.get_url(ctx, 'forms', 'load_file')}">${_(u'Open Form')}</a></li>
                    </ul>
                    <%self:topbar_user/>
                </div>
            </div>
        </div>
    </div>
</%def>


<%def name="topbar_dropdown_admin()" filter="trim">
##    % if model.is_admin(ctx):
##                        <li class="dropdown" id="topbar-admin-menu">
##                            <a class="dropdown-toggle" data-toggle="dropdown" href="#topbar-admin-menu">${_('Administration')} <b class="caret"></b></a>
##                            <ul class="dropdown-menu">
##                                <li><a href="${model.Account.get_admin_class_url(ctx)}">${_('Accounts')}</a></li>
##                                <li><a href="${model.Form.get_admin_class_url(ctx)}">${_('Forms')}</a></li>
##                                <li><a href="${model.Project.get_admin_class_url(ctx)}">${_('Projects')}</a></li>
##                                <li><a href="${model.Session.get_admin_class_url(ctx)}">${_('Sessions')}</a></li>
##                                <li><a href="${model.Subscription.get_admin_class_url(ctx)}">${_('Subscriptions')}</a></li>
##                            </ul>
##                        </li>
##    % endif
</%def>


<%def name="topbar_user()" filter="trim">
##                    <ul class="nav pull-right">
##<%
##    user = model.get_user(ctx)
##%>\
##    % if user is None:
##                        <li><a href="javascript:poptastic(${urls.get_url(ctx, 'login', callback = req.path_qs, popup = 1
##                                ) | n, js, h})">${_(u'Sign In')}</a></li>
##    % else:
####                        <li class="active"><a href="${user.get_url(ctx)}"><i class="icon-user icon-white"></i> ${user.email}</a></li>
##                        <li class="active"><a href="#"><i class="icon-user icon-white"></i> ${user.get_title(ctx)}</a></li>
##                        <li><a href="${urls.get_url(ctx, 'logout', callback = req.path_qs)}">${_('Sign Out')}</a></li>
##    % endif
##                    </ul>
</%def>


<%def name="trackers()" filter="trim">
    % if 'google_analytics_key' in conf:
        <script type="text/javascript">
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
        </script>
        <script type="text/javascript">
try {
    var pageTracker = _gat._getTracker("${conf['google_analytics_key']}");
    pageTracker._trackPageview();
} catch(err) {}
        </script>
    % endif
</%def>


<!DOCTYPE html>
<html lang="${ctx.lang[0][:2]}">
<head>
    <%self:metas/>
    <title>${self.title_content()}</title>
    <%self:css/>
    <%self:feeds/>
</head>
<body>
    <%self:topbar/>
    <%self:body_content/>
    <%self:scripts/>
    <%self:trackers/>
</body>
</html>

