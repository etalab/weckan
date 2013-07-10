<%!
from biryani1 import strings

from weckan import urls

from weckan.model import meta, Package
%>


<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Emploi & formation professionnelle | Data.Gouv.fr</title>
<base href="http://devserver.me/datagouv/index.php">
<meta name="robots" content="noindex, nofollow">
<meta name="description" content="Document sans nom">
<meta name="author" content="Anonymous" />
<meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no">
<link rel="shortcut icon" type="image/x-icon" href="img/favicon.ico" />
<link rel="stylesheet" media="screen" href="css/style.css">
<link rel="stylesheet" media="screen" href="css/chosen.css">
</head>
<body>

<header class="mainheader">
    <a href="index.php">
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
                            <li><a href="productor.php">Producteurs</a></li>
                            <li><a href="#">Licence Ouverte</a></li>
                            <li><a href="#">Quelles données ?</a></li>
                            <li><a href="#">ETALAB</a></li>
                        </ul>
                    </li>
                    <li>
                        <span>Actualités</span>
                    </li>
                </ul>
            </li>

            <!-- Search -->
            <li class="nav_search">
                <ul>
                    <li class="searchnav">
                        <form action="#">
                            <input type="search" placeholder="Rechercher..." />
                            <input type="submit" value="&#xe00a;">
                        </form>
                    </li>
                    <li class="results_search">
                        <span>Appuyez sur Entrée pour lancer la recherche...</span>
                        <ul class="q_datas">
                            <li>
                                <span>Jeux de données</span>
                                <ul>
                                    <li><a href="data.php">Taux de chômage</a></li>
                                    <li><a href="data.php">Criminalité dans les villes</a></li>
                                </ul>
                            </li>
                            <li>
                                <span>Producteurs</span>
                                <ul>
                                    <li><a href="productor.php">INSEE</a></li>
                                    <li><a href="productor.php">Mairie de Paris</a></li>
                                </ul>
                            </li>
                        </ul>
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
                        <span><a href="${urls.get_full_url(ctx, 'group', strings.slugify(group_title))}">${group_title}</a></span>
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
        <ul class="top_breadcrumb">
            <li><a href="rubric.php" class="prev_breadcrumb">Emploi et formation professionnelle</a></li>
        </ul>
        <ul class="top_actions">
            <li class="actions_profilmenu noconnected">
                <span>Connexion / Inscription</span>
                <ul>
                    <form action="me.php">
                    <li>
                        <input type="text" placeholder="Adresse e-mail">
                    </li>
                    <li>
                        <input type="text" placeholder="Mot de passe">
                    </li>
                    <li>
                        <input type="submit" value="Connexion" class="bt_connect">
                    </li>
                    </form>
                    <li><a href="#" class="problem_account">Je n'arrive pas à me connecter</a></li>
                    <li><a href="#" class="create_account">Créer un compte</a></li>
                </ul>
            </li>
        </ul>
    </nav>
</section>
    <div class="contentpage">
        
        <div class="home_featured">
            <a href="#">
            <div class="home_gradient"></div>
            <span>À la une</span>
            <h1><a href="#" class="titlenews">Le G8 signe une Charte pour l’Ouverture des Données Publiques</a></h1>
            </a>
        </div>

        <div class="home_feeds">
            <ul class="home_feeds_tabs">
                <li data-tab="last_data" class="active">Dernières données</li>
                <li data-tab="last_news">Dernières acualités</li>
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
                <ul class="last_data active">
                    <li><span class="data_add"></span><a href="data.php">Taux de chomage<span>a été ajouté</span></a><span class="feed_date">25/06/2013</span></li>
                    <li><span class="data_update"></span><a href="data.php">Recensement population <span>a été mis à jour</span></a><span class="feed_date">23/06/2013</span></li>
                    <li><span class="data_add"></span><a href="data.php">Espaces verts <span>a été ajouté</span></a><span class="feed_date">17/06/2013</span></li>
                    <li><span class="data_add"></span><a href="data.php">Qualité de l'eau <span>a été ajouté</span></a><span class="feed_date">17/06/2013</span></li>
                    <li><span class="data_add"></span><a href="data.php">Insertion des diplômés <span>a été ajouté</span></a><span class="feed_date">08/06/2013</span></li>
                    <li><span class="data_update"></span><a href="data.php">Résultats présidentielles <span>a été mis à jour</span></a><span class="feed_date">02/06/2013</span></li>
                    <li><span class="data_update"></span><a href="data.php">Répartition logements <span>a été mis à jour</span></a><span class="feed_date">28/05/2013</span></li>
                    <li><span class="data_add"></span><a href="data.php">Commerce extérieur <span>a été mis à jour</span></a><span class="feed_date">23/05/2013</span></li>
                </ul>
            </div>
        </div>

        <!-- DESCRIPTION -->
        <section class="description_home">
            <ul>
                <li>
                    <a href="#">
                    <img src="img/ico1.png" alt="Données publiques" width="84" height="84" />
                    <h2>Données publiques</h2>
                    <p>Les données publiques sont l’ensemble des données de la cité publiées ou tenues à disposition du public, qui sont produites ou collectées par une collectivité, un organisme ou un service public.</p>
                    </a>
                </li>
                <li>
                    <a href="#">
                    <img src="img/ico2.png" alt="Producteurs de données" width="84" height="84" />
                    <h2>Producteurs de données</h2>
                    <p>Les prodcuteurs de données, qu'ils soient des organismes ou des administrations, contribuent à l'élaboration de l'open gouvernance en redistribuant les données dans l'espace publique.</p>
                    </a>
                </li>
                <li>
                    <a href="#">
                    <img src="img/ico3.png" alt="Etalab" width="84" height="84" />
                    <h2>Etalab</h2>
                    <p>Au sein du Secrétariat général pour la modernisation de l’action publique, Etalab coordonne l’action des services de l’Etat et de ses établissements publics pour faciliter la réutilisation.</p>
                    </a>
                </li>
            </ul>
        </section>

        <!-- PROJECTS -->
        <section class="projects_block home">
            <h1>Projets à la une</h1>
            <ul>
                <li>
                    <figure style="background-image:url(img/wdmtg.png)"></figure>
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
                    <figure style="background-image:url(img/rennes.png)"></figure>
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
                    <figure style="background-image:url(img/dataparis.png)"></figure>
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

<script src="js/lib/jquery-2.0.0.min.js"></script>
<script src="js/main.js"></script>
</body>
</html>
