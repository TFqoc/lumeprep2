console.log("Live Timer has been loaded 1v");
odoo.define('timer.live_timer', function (require) {
    "use strict";
    
    var fieldRegistry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var Timer = require('timer.Timer');
    
    var LiveTimerFieldWidget = AbstractField.extend({
    
        init: function (parent, name, record, options) {
            this._super.apply(this, arguments);
            let my_options = options.attrs || {};
            my_options = my_options.options || {};
            this.flash = my_options.flash || false;
            this.color_class = my_options.color_class || '';
            this.className = `o_field_widget o_readonly_modifier ${this.color_class} ml-auto h5 ml-4 font-weight-bold`;
        },
        /**
         * @override
         * @private
         */
        isSet: function () {
            return true;
        },
        /**
         * @override
         * @private
         */
        _render: function () {
            this._super.apply(this, arguments);
            if (!this.flash){
                this.$el.css("float", "right");
            }
            this._startTimeCounter();
        },
        /**
         * @override
         */
        destroy: function () {
            this._super.apply(this, arguments);
            clearInterval(this.timer);
        },
        /**
         * @private
         */
        _startTimeCounter: async function () {
            if (this.value) {
                console.log("Time now: " + this.record.data.time_now);
                const serverTime = this.record.data.time_now || await this._getServerTime();
                this.time = Timer.createTimer(0, this.value, serverTime);
                this.$el.text(this.time.toString());
                this.timer = setInterval(() => {
                    if (this.record.data.timer_pause) {
                        clearInterval(this.timer);
                    } else {
                        this.time.addSecond();
                        this.$el.text(this.time.toString());
                        if (this.flash){
                            this.blinking = this.time.convertToSeconds() / 60 >= this.record.data.blink_threshold;
                            if (this.blinking){
                                this.$el.toggleClass('timer-normal');
                                this.$el.toggleClass('timer-flash');
                            }
                        }
                    }
                }, 1000);
            } else if (!this.record.data.timer_pause){
                clearInterval(this.timer);
            }
        },
        _getServerTime: function () {
            return this._rpc({
                model: 'timer.timer',
                method: 'get_server_time',
                args: []
            });
        }
    });
    
    fieldRegistry.add('live_timer', LiveTimerFieldWidget);
    
    });
    
