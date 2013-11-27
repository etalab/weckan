/**
 * Dataset page specific features
 */
(function($) {

    "use strict";

    var ws_url = $('.metrics-container').data('ws-url');

    function updateValue(id, value) {
        $('#' + id + ' .metric-value').fadeOut("slow", function(){
            $(this).text(value).fadeIn("slow");
        });
    }

    function startWebSocket() {
        var ws;

        if (window.WebSocket) {
            ws = new WebSocket(ws_url);
        } else if (window.MozWebSocket) {
            ws = MozWebSocket(ws_url);
        } else {
            console.log('WebSocket Not Supported');
            return;
        }

        window.onbeforeunload = function(e) {
            ws.close(1000, 'Left the room');

            if (!e) {
                e = window.event;
            }
            e.stopPropagation();
            e.preventDefault();
        };

        ws.onclose = function(evt) {
            // Try to reconnect in 5 seconds.
            setTimeout(startWebSocket, 5000);
        };

        ws.onmessage = function(evt) {
            var data = $.parseJSON(evt.data);
            console.debug(data);
            updateValue(data.metric, data.value);
        };
    }

    window.updateValue = updateValue;

    $(function() {
        startWebSocket();
    });

}(window.jQuery));
