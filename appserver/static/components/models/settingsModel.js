define([
    'underscore',
    'backbone',
], function (_, Backbone) {
    "use strict";

    var SettingsModel = Backbone.Model.extend({

        defaults: {
            keys: {},
            failed: false,
            error: "",
            test: "",
            loaded: false
        }

    });

    return new SettingsModel();

});