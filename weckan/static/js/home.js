/**
 * Homepage specific features
 */
(function($){

    "use strict";

    $('#home-carousel .title').on('slide.bs.carousel', function() {
        $(this).trigger('update');
    });

}(window.jQuery));
