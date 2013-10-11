/**
 * Dataset page specific features
 */
(function($, swig){

    "use strict";

    var COW_URL = $('link[rel="cow"]').attr('href'),
        COW_API_URL = COW_URL + '/api/1/datasets/{name}/ranking';

    $(function() {
        var name = $('meta[name="dataset-name"]').attr('content'),
            url = COW_API_URL.replace('{name}', name);

        // Fetch ranking
        $.get(url, function(data) {
            var weight = data.value.weight.toFixed(3),
                tpl = swig.compile($('#quality-template').text());

            $('#infos-list').append(tpl({ weight: weight}));
        });
    });

}(window.jQuery, window.swig));
