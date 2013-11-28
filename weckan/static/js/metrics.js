/**
 * Dataset page specific features
 */
(function($, WebSocket) {

    "use strict";

    var ws_url = $('.metrics-container').data('ws-url');

    function updateValue(id, value) {
        var $div = $('#' + id + ' .metric-value');

        if ($div.text() != value) {
            $div.fadeOut("slow", function(){
                $(this).text(value).fadeIn("slow");
            });
        }
    }

    function startWebSocket() {
        var ws;

        if (WebSocket) {
            ws = new WebSocket(ws_url);
        // } else if (window.MozWebSocket) {
        //     ws = MozWebSocket(ws_url);
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
            for (var key in data) {
                updateValue(key, data[key]);
            }
        };

        ws.onerror = function(error) {
            console.error('WS error', error);
        };
    }

    $(function() {
        startWebSocket();
    });

}(window.jQuery, window.WebSocket));
