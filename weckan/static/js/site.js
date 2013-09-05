/**
 * Site-wide features, helpers and fixes
 */
(function($){

    "use strict";

    var TERRYTORIES_END_POINT = 'http://ou.comarquage.fr/api/v1/autocomplete-territory',
        TERRITORIES_KIND = [
            'ArrondissementOfCommuneOfFrance',
            'CommuneOfFrance',
            'Country',
            'DepartmentOfFrance',
            'OverseasCollectivityOfFrance',
            'RegionOfFrance'
        ],
        API_URL = TERRYTORIES_END_POINT + '?' + $.param({ kind: TERRITORIES_KIND, term: '_QUERY'}, true),
        COOKIE_NAME = 'territory-infos';

    /**
     * Filter the Territory API to match Typeahead expected format.
     */
    var filter_territory_api = function(response) {
        return response.data.items;
    };

    /**
     * Fix JSONP compatibility between API and typeahead.js
     */
    var fix_url = function(jqXhr, settings) {
        settings.url = settings.url.replace('callback', 'jsonp');
    };

    /**
     * Set the territory to filter
     * @param {string} value   the territory key (kind/code)
     * @param {string} display the territory display name
     */
    var set_territory = function(value, display) {
        $('#ext_territory').val(value);
        if (display) {
            $('#where-input').val(display);
        } else {
            display = $('#where-input').val();
        }

        $('#where-group .glyphicon')
            .removeClass('glyphicon-globe')
            .addClass('glyphicon-remove')
            .addClass('territory-clear');

        // Persist the filter into the cookie
        $.cookie(COOKIE_NAME, value + '|' + display, {path: '/'});
    };

    /**
     * Clear the current territory filter
     */
    var clear_territory = function() {
        $.removeCookie(COOKIE_NAME, {path: '/'});
        $('#where-input').val(null);
        $('#ext_territory').val(null);
        $('#where-group .glyphicon')
            .removeClass('glyphicon-remove')
            .removeClass('territory-clear')
            .addClass('glyphicon-globe');
    }


    $(function() {
        // Force cookie raw
        $.cookie.raw = true;

        // Fix collapse on sidebar
        $("#sidebar .panel-heading a").on('click', function (e) { e.preventDefault(); });

        // Display tooltips and popovers
        $('[rel=tooltip]').tooltip();
        $('[rel=popover]').popover();

        // Search field behavior
        $('#where-input')
            .typeahead({
                name: 'territories',
                valueKey: 'main_postal_distribution',
                remote: {
                    url: API_URL,
                    wildcard: '_QUERY',
                    dataType: 'jsonp',
                    filter: filter_territory_api,
                    beforeSend: fix_url
                }
            })
            .on('typeahead:selected typeahead:autocompleted', function(e, territory) {
                set_territory(territory.kind + '/' + territory.code);
                $('#search-input').focus();
            })
            ;

        $('#where-group').on('click', '.territory-clear', clear_territory);

        // Restore territory state from cookie
        if ($.cookie(COOKIE_NAME)) {
            set_territory.apply(null, $.cookie(COOKIE_NAME).split('|'));
        }
    });


}(window.jQuery));
