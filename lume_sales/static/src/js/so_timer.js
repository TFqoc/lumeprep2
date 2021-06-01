odoo.define('lume_sales.so_timer', function (require) {
    "use strict";
    
    var fieldRegistry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var Timer = require('timer.Timer');
    
    var SOTimer = AbstractField.extend({
    
        init: function (parent, name, record, options) {
            this._super.apply(this, arguments);
            this.className = 'o_field_widget o_readonly_modifier text-success ml-auto h5 ml-4 font-weight-bold';
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
            if (this.record.data.timer_start) {
                const serverTime = await this._getServerTime();
                this.time = Timer.createTimer(0, this.record.data.timer_start, serverTime);
                this.$el.text(this.time.toString());
                this.timer = setInterval(() => {
                    if (this.record.data.timer_pause) {
                        clearInterval(this.timer);
                    } else {
                        this.time.addSecond();
                        this.$el.text(this.time.toString());
                        let minutes = this.time.convertToSeconds() / 60
                        if (minutes >= this.record.data.threshold1 && minutes < this.record.data.threshold2){
                            this.$el.css('color','yellow');
                        }
                        else if (minutes >= this.record.data.threshold2 && minutes < this.record.data.threshold3){
                            this.$el.css('color','orange');
                        }
                        else if (minutes >= this.record.data.threshold3){
                            this.$el.css('color','red');
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
    
    fieldRegistry.add('so_timer', SOTimer);
    
    });
    
