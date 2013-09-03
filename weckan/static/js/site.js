/**
 * Site-wide features, helpers and fixes
 */
(function($){

    "use strict";

    $(function() {
        // Fix collapse on sidebar
        $("#sidebar .panel-heading a").on('click', function (e) { e.preventDefault(); });

        // Display tooltips
        $('[rel=tooltip]').tooltip();
        $('[rel=popover]').popover();
    });


}(window.jQuery));
