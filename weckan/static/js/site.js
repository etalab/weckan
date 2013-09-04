/**
 * Site-wide features, helpers and fixes
 */
(function($){

    "use strict";

    var hide_where = function() {
        if (!$('#where-group input').val() && !$('#where-group input').is(':focus')) {
            $('#where-group').collapse('hide');
        }
    }


    $(function() {
        // Fix collapse on sidebar
        $("#sidebar .panel-heading a").on('click', function (e) { e.preventDefault(); });

        // Display tooltips
        $('[rel=tooltip]').tooltip();
        $('[rel=popover]').popover();

        // Search field behavior
        $('#search-input').on('focus', function() {
            $('#where-group').collapse('show');
        }).on('blur', function() {
            setTimeout(hide_where, 500);
        });

        $('#where-group input').on('blur', hide_where);
    });


}(window.jQuery));
