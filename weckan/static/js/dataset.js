/**
 * Dataset page specific features
 */
(function($, swig){

    "use strict";

    var QUALITY_PRECISION = 2,
        COW_URL = $('link[rel="cow"]').attr('href'),
        COW_API_URL = COW_URL + '/api/1/datasets/{name}/ranking';

    $(function() {
        var name = $('meta[name="dataset-name"]').attr('content'),
            url = COW_API_URL.replace('{name}', name);

        // Fetch ranking
        $.get(url, function(data) {
            var weight = data.value.weight,
                tpl = swig.compile($('#quality-template').text());

            if (weight) {
                var $list = $('#infos-list');
                $list.append(tpl({
                    weight: weight.toFixed(QUALITY_PRECISION),
                    url: data.value.url,
                    errors: data.value.error || 0,
                    warnings: data.value.warning || 0
                }))
                .find('.quality-report [rel=tooltip]').tooltip();
                $list.find('.quality-report [rel=popover]').popover();
            }
        });
    });

}(window.jQuery, window.swig));
