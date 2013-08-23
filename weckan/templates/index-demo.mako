<%!
import json

from biryani1 import strings
from  sqlalchemy.sql import func

from weckan import urls

from weckan.model import Activity, meta, Package
%>


<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Data.Gouv.fr</title>
<meta name="robots" content="noindex, nofollow">
<meta name="description" content="Document sans nom">
<meta name="author" content="Anonymous" />
<meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no">
<link rel="shortcut icon" type="image/x-icon" href="/hetic/img/favicon.ico" />
<link rel="stylesheet" media="screen" href="/hetic/css/style.css">
<link rel="stylesheet" media="screen" href="/hetic/css/chosen.css">
</head>
<body>

<header class="mainheader">
    <a href="${urls.get_url(ctx)}">
        <h1>Data.Gouv.fr</h1>
        <span>Innovation, transparence, ouverture</span>
    </a>
    
    <nav class="mainnav">
        <ul>

            <!-- Static -->
            <li class="nav_pages">
                <ul>
                    <li>
                        <span>Données publiques</span>
                        <ul>
                            <li><a href="#">Définition</a></li>
                            <li><a href="${urls.get_url(ctx, 'organization')}">Producteurs</a></li>
                            <li><a href="http://www.etalab.gouv.fr/pages/licence-ouverte-open-licence-5899923.html">Licence Ouverte</a></li>
                            <li><a href="#">Quelles données ?</a></li>
                            <li><a href="http://www.etalab.gouv.fr/">ETALAB</a></li>
                        </ul>
                    </li>
##                    <li>
##                        <span>Actualités</span>
##                    </li>
                </ul>
            </li>

            <!-- Search -->
            <li class="nav_search">
                <ul>
                    <li class="searchnav">
                        <form action="${urls.get_url(ctx, 'dataset')}">
                            <input name="q" type="search" placeholder="Rechercher..." />
                            <input type="submit" value="&#xe00a;">
                        </form>
                    </li>
                </ul>
            </li>
            

            <!-- Rubrics -->
            <li class="nav_rubrics">
                <ul>
<%
    groups_title = [
        u"Culture et communication",
        u"Développement durable",
        u"Éducation et recherche",
        u"État et collectivités",
        u"Europe",
        u"Justice",
        u"Monde",
        u"Santé et solidarité",
        u"Sécurité et défense",
        u"Société",
        u"Travail, économie, emploi",
        ]
%>\
    % for group_title in groups_title:
                    <li>
                        <span><a href="${urls.get_url(ctx, 'group', strings.slugify(group_title))}">${group_title}</a></span>
                    </li>
    % endfor
                </ul>
            </li>

        </ul>
    </nav>
</header>
<div class="maincontent" data-page="home">
    
    <div class="opacitycontent"></div>

<section class="topbar">
    <nav>
        <ul class="top_actions">
            <li class="actions_profilmenu noconnected">
                <span>Connexion / Inscription</span>
                <ul>
                    <li><a href="${urls.get_url(ctx, 'user', 'login')}" class="create_account">Connexion</a></li>
                    <li><a href="${urls.get_url(ctx, 'user', 'register')}" class="create_account">Créer un compte</a></li>
                </ul>
            </li>
        </ul>
</section>
    </nav>
    <div class="contentpage">

         <p style="font-family: 'ProximaNova'; font-size: 2em; line-height: 1.2em; padding-bottom: 1em">Ici, les acteurs publics <strong>co-construisent</strong> avec la société civile une <strong>vision partagée</strong> de la France qui stimule l'<strong>innovation</strong>.</p>
       
        <div class="home_featured" style="width: calc(55% - 30px); height: 320px; float: left; border-radius: 4px 4px 4px 4px; background: url(http://i-cms.journaldesfemmes.com/image_cms/original/1167773.jpg) repeat scroll 0% 0% transparent; position: relative; overflow: hidden; font-family: 'ProximaNova'; color: rgb(244, 244, 244)">
            <a href="http://wiki.etalab2.fr/wiki/L%27%C3%A9galit%C3%A9_Femmes_Hommes">
            <div class="home_gradient"></div>
            <span>À la une</span>
            <h1><a href="http://wiki.etalab2.fr/wiki/L%27%C3%A9galit%C3%A9_Femmes_Hommes" class="titlenews">Projet de loi pour l’égalité entre les femmes et les hommes</a></h1>
            </a>
        </div>

        <div class="home_feeds">
            <ul class="home_feeds_tabs">
                <li data-tab="best_data" class="active">Les plus<br>consultées</li>
                <li data-tab="last_data">Dernières<br>données</li>
                <li data-tab="last_news">Dernières<br>actualités</li>
            </ul>
            <div class="home_feeds_content">
                <ul class="last_news">
                    <li><a href="#">Remise des prix DataConnexions #3</a><span class="feed_date news">22/06/2013</span></li>
                    <li><a href="#">Le G8 signe une Charte pour l’Ouverture des Données Publiques</a><span class="feed_date news">16/06/2013</span></li>
                    <li><a href="#">Datajournalisme : Des données pour s’informer</a><span class="feed_date news">12/06/2013</span></li>
                    <li><a href="#">Contribution de data publica à la consultation codesign</a><span class="feed_date news">05/06/2013</span></li>
                    <li><a href="#">Lancement de la phase 2 du codesign</a><span class="feed_date news">27/05/2013</span></li>
                    <li><a href="#">Etalab lance le codesign du prochain data.gouv.fr</a><span class="feed_date news">23/05/2013</span></li>
                    <li><a href="#">Les entreprises publiques à l’heure de l’open data</a><span class="feed_date news">17/05/2013</span></li>
                    <li><a href="#">Openstreetmap complète sa carte du monde interactive</a><span class="feed_date news">11/05/2013</span></li>
                </ul>
                <ul class="last_data">
    % for activity in meta.Session.query(Activity).filter(Activity.activity_type.in_(['changed package', 'new package'])).order_by(Activity.timestamp.desc()).limit(8):
<%
        package = activity.data['package']
        title = package['title']
        if len(title) > 80:
            title = title[:77] + u'...'
%>\
                    <li><span class="${'data_add' if activity.activity_type == 'new package' else 'data_update'}"></span><a href="${urls.get_url(ctx, 'dataset', package['name'])}">${title}<span>a été ${u'ajouté'  if activity.activity_type == 'new package' else u'modifié'}</span></a><span class="feed_date">${activity.timestamp.isoformat().split('T')[0]}</span></li>
    % endfor
                </ul>
                <ul class="best_data active">
    % for package in meta.Session.query(Package).order_by(func.random()).limit(8):
                    <li><a href="${package.get_url(ctx)}">${package.title}</a></li>
    % endfor
                </ul>
            </div>
        </div>

        <!-- DESCRIPTION -->
        <section class="description_home">
##            <ul>
##                <li>
##                    <a href="${urls.get_url(ctx, 'dataset')}">
##                    <img src="/hetic/img/ico1.png" alt="Données publiques" width="84" height="84" />
##                    <h2>Données publiques</h2>
##                    <p>Les données publiques sont l’ensemble des données de la cité publiées ou tenues à disposition du public, qui sont produites ou collectées par une collectivité, un organisme ou un service public.</p>
##                    </a>
##                </li>
##                <li>
##                    <a href="${urls.get_url(ctx, 'organization')}">
##                    <img src="/hetic/img/ico2.png" alt="Producteurs de données" width="84" height="84" />
##                    <h2>Producteurs de données</h2>
##                    <p>Les prodcuteurs de données, qu'ils soient des organismes ou des administrations, contribuent à l'élaboration de l'open gouvernance en redistribuant les données dans l'espace publique.</p>
##                    </a>
##                </li>
##                <li>
##                    <a href="http://www.etalab.gouv.fr/">
##                    <img src="/hetic/img/ico3.png" alt="Etalab" width="84" height="84" />
##                    <h2>Etalab</h2>
##                    <p>Au sein du Secrétariat général pour la modernisation de l’action publique, Etalab coordonne l’action des services de l’Etat et de ses établissements publics pour faciliter la réutilisation.</p>
##                    </a>
##                </li>
##            </ul>
        </section>

        <!-- PROJECTS -->
        <section class="projects_block home">
            <h1>À la une</h1>
            <ul>
##                <li>
##                    <figure style="background-image:url(https://dl.dropboxusercontent.com/u/2194909/egaliteHF.png)"></figure>
##                    <div class="project_view">
##                        <a href="http://wiki.etalab2.fr/wiki/L%27%C3%A9galit%C3%A9_Femmes_Hommes">Accéder</a>
##                    </div>
##                    <div class="project_txt">
##                    <div>
##                        <h2>Égalité Femmes Hommes</h2>
##                        <p>Projet de loi pour l’égalité entre les femmes et les hommes. </p>
##                    </div>
##                    </div>
##                </li>
                <li>
                    <figure style="background-image:url(/hetic/img/wdmtg.png)"></figure>
                    <div class="project_view">
                        <a href="http://wdmtg.com/">Accéder au projet</a>
                    </div>
                    <div class="project_txt">
                    <div>
                        <h2>Where Does My Tweet Go?</h2>
                        <p>Interface de visualisation, au travers d'un graph, de l'influence d'un tweet et des influenceurs.</p>
                    </div>
                    </div>
                </li>
                <li>
                    <figure style="background-image:url(/hetic/img/rennes.png)"></figure>
                    <div class="project_view">
                        <a href="http://dataviz.rennesmetropole.fr/quisommesnous/index-fr.php">Accéder au projet</a>
                    </div>
                    <div class="project_txt">
                    <div>
                        <h2>Métropole Rennes</h2>
                        <p>Interface de visualisation destinée à faire un portrait des habitants de Rennes Métropole à partir de données ouvertes.</p>
                    </div>
                    </div>
                </li>
                <li>
                    <figure style="background-image:url(/hetic/img/dataparis.png)"></figure>
                    <div class="project_view">
                        <a href="http://dataparis.io">Accéder au projet</a>
                    </div>
                    <div class="project_txt">
                    <div>
                        <h2>DataParis.io</h2>
                        <p>Des données sur Paris et les Parisiens loclisées par le biais du réseau métropolitain</p>
                    </div>
                    </div>
                </li>
            </ul>
        </section>
        
    </div>

</div>

<script src="/hetic/js/lib/jquery-2.0.0.min.js"></script>
<script src="/hetic/js/main.js"></script>
</body>
</html>
