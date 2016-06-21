(function (factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD
        define(['jquery'], factory);
    } else if (typeof exports === 'object') {
        // CommonJS
        factory(require('jquery'));
    } else {
        // Browser globals
        factory(jQuery);
    }
}(function ($) {
  var CountTo = function (element, options) {
    this.$element = $(element);
    this.options  = $.extend({}, CountTo.DEFAULTS, this.dataOptions(), options);
    this.init();
  };

  CountTo.DEFAULTS = {
    from: 0,               // the number the element should start at
    to: 0,                 // the number the element should end at
    speed: 1000,           // how long it should take to count between the target numbers
    refreshInterval: 100,  // how often the element should be updated
    decimals: 0,           // the number of decimal places to show
    formatter: formatter,  // handler for formatting the value before rendering
    onUpdate: null,        // callback method for every time the element is updated
    onComplete: null       // callback method for when the element finishes updating
  };

  CountTo.prototype.init = function () {
    this.value     = this.options.from;
    this.loops     = Math.ceil(this.options.speed / this.options.refreshInterval);
    this.loopCount = 0;
    this.increment = (this.options.to - this.options.from) / this.loops;
  };

  CountTo.prototype.dataOptions = function () {
    var options = {
      from:            this.$element.data('from'),
      to:              this.$element.data('to'),
      speed:           this.$element.data('speed'),
      refreshInterval: this.$element.data('refresh-interval'),
      decimals:        this.$element.data('decimals')
    };

    var keys = Object.keys(options);

    for (var i in keys) {
      var key = keys[i];

      if (typeof(options[key]) === 'undefined') {
        delete options[key];
      }
    }

    return options;
  };

  CountTo.prototype.update = function () {
    this.value += this.increment;
    this.loopCount++;

    this.render();

    if (typeof(this.options.onUpdate) == 'function') {
      this.options.onUpdate.call(this.$element, this.value);
    }

    if (this.loopCount >= this.loops) {
      clearInterval(this.interval);
      this.value = this.options.to;

      if (typeof(this.options.onComplete) == 'function') {
        this.options.onComplete.call(this.$element, this.value);
      }
    }
  };

  CountTo.prototype.render = function () {
    var formattedValue = this.options.formatter.call(this.$element, this.value, this.options);
    this.$element.text(formattedValue);
  };

  CountTo.prototype.restart = function () {
    this.stop();
    this.init();
    this.start();
  };

  CountTo.prototype.start = function () {
    this.stop();
    this.render();
    this.interval = setInterval(this.update.bind(this), this.options.refreshInterval);
  };

  CountTo.prototype.stop = function () {
    if (this.interval) {
      clearInterval(this.interval);
    }
  };

  CountTo.prototype.toggle = function () {
    if (this.interval) {
      this.stop();
    } else {
      this.start();
    }
  };

  function formatter(value, options) {
    return value.toFixed(options.decimals);
  }

  $.fn.countTo = function (option) {
    return this.each(function () {
      var $this   = $(this);
      var data    = $this.data('countTo');
      var init    = !data || typeof(option) === 'object';
      var options = typeof(option) === 'object' ? option : {};
      var method  = typeof(option) === 'string' ? option : 'start';

      if (init) {
        if (data) data.stop();
        $this.data('countTo', data = new CountTo(this, options));
      }

      data[method].call(data);
    });
  };
}));



/* ---------- Temp Stats ---------- */

function tempStats(){

	if($('.tempStat')) {
		
		$('.tempStat').each(function(){
			
			var temp = Math.floor(Math.random()*(1+120));
			
			$(this).html(temp + '°');
						
			if (temp < 20) {
				
				$(this).animate({
				            borderColor: "#67c2ef"
				        }, 'fast');
				
			} else if (temp > 19 && temp < 40) {
				
				$(this).animate({
				            borderColor: "#CBE968"
				        }, 'slow');
				
			} else if (temp > 39 && temp < 60) {
				
				$(this).animate({
				            borderColor: "#eae874"
				        }, 'slow');

			} else if (temp > 59 && temp < 80) {
				
				$(this).animate({
				            borderColor: "#fabb3d"
				        }, 'slow');

			} else if (temp > 79 && temp < 100) {

				$(this).animate({
				            borderColor: "#fa603d"
				        }, 'slow');

			} else {
				
				$(this).animate({
				            borderColor: "#ff5454"
				        }, 'slow');
				
			}
			
		});
		
	}
	
}

setInterval(tempStats, 3000);

$(document).ready(function(){
	
	/* ---------- Init jQuery Knob - disbaled in IE8, IE7, IE6 ---------- */
	if(jQuery.browser.version.substring(0, 2) == "8.") {
		 
		//disable jQuery Knob
		
	} else {
	
		if (retina()) {

			$(".whiteCircle").knob({
		        'min':0,
		        'max':100,
		        'readOnly': true,
		        'width': 240,
		        'height': 240,
				'bgColor': 'rgba(255,255,255,0.5)',
		        'fgColor': 'rgba(255,255,255,0.9)',
		        'dynamicDraw': true,
		        'thickness': 0.2,
		        'tickColorizeValues': true
		    });
			
			$(".orangeCircle").knob({
				'min':0,
		        'max':100,
		        'readOnly': true,
		        'width': 240,
		        'height': 240,
				'bgColor': 'rgba(255,255,255,0.5)',
		        'fgColor': 'rgba(234, 70, 16, 0.901961)',
		        'dynamicDraw': true,
		        'thickness': 0.2,
		        'tickColorizeValues': true
			});

			//only firefox sux in this case
			if (jQuery.browser.mozilla) {
				$(".circleStat").css('MozTransform','scale(0.5,0.5)');
				$(".whiteCircle").css('MozTransform','scale(0.999,0.999)');
				$(".whiteCircle").css('margin-top','20px');
				$(".circleStat").css('margin-top','-60px').css('margin-left','-36px');
			} else {
				$(".circleStat").css('zoom',0.5);
				$(".whiteCircle").css('zoom',0.999);
			}			

		} else {

			$(".whiteCircle").knob({
		        'min':0,
		        'max':100,
		        'readOnly': true,
		        'width': 120,
		        'height': 120,
				'bgColor': 'rgba(255,255,255,0.5)',
		        'fgColor': 'rgba(255,255,255,0.9)',
		        'dynamicDraw': true,
		        'thickness': 0.2,
		        'tickColorizeValues': true
		    });
			
			$(".orangeCircle").knob({
				'min':0,
		        'max':100,
		        'readOnly': true,
		        'width': 120,
		        'height': 120,
				'bgColor': 'rgba(255,255,255,0.5)',
		        'fgColor': 'rgba(234, 70, 16, 0.901961)',
		        'dynamicDraw': true,
		        'thickness': 0.2,
		        'tickColorizeValues': true
			});

		}
		
		$(".circleStatsItemBox").each(function(){

			var value = $(this).find(".value > .number").html();
			var unit = $(this).find(".value > .unit").html();
			var percent = $(this).find("input").val()/100;

			countSpeed = 2300*percent;

			endValue = value*percent;

			$(this).find(".count > .unit").html(unit);
			$(this).find(".count > .number").countTo({

				from: 0,
			    to: endValue,
			    speed: countSpeed,
			    refreshInterval: 50,
			    onComplete: function(value) {
			    	console.debug(this);
			    }

			});

		});
	
	}
	
	/* ---------- Active Users Chart ---------- */
	
	if($("#activeUsers").length) {
	    var d1 = [];
	    
	    for (var i = 0; i <= 160; i += 1) {
	        d1.push([i, parseInt(Math.random() * 123123)]);
		}	

	    var stack = 0, bars = true, lines = false, steps = false;

	    function plotWithOptions2() {
					
	        $.plot($("#activeUsers"), [ d1 ], {
	            series: {
	                bars: { show: bars, 
							fill: true, 
							barWidth: 0.1, 
							align: "center",
							lineWidth: 5,
							fillColor: { colors: [ { opacity: 1 }, { opacity: 0.5 } ] }
						},
	            },
				grid: { hoverable: true, 
						   clickable: true, 
						   tickColor: "#f6f6f6",
						   borderWidth: 0,
						},
				colors: ["#CBE968"],
				xaxis: {ticks:0, tickDecimals: 0, tickFormatter: function(v, a) {return v }},
				yaxis: {ticks:5, tickDecimals: 0, tickFormatter: function (v) { return v }},
	
	        });
	    }
	
	    plotWithOptions2();

	}
	
	/* ---------- Realtime chart - Server Load Chart ---------- */
	var data = [], totalPoints = 300;
	function getRandomData() {
		if (data.length > 0)
			data = data.slice(1);

		// do a random walk
		while (data.length < totalPoints) {
			var prev = data.length > 0 ? data[data.length - 1] : 50;
			var y = prev + Math.random() * 10 - 5;
			if (y < 0)
				y = 0;
			if (y > 100)
				y = 100;
			data.push(y);
		}

		// zip the generated y values with the x values
		var res = [];
		for (var i = 0; i < data.length; ++i)
			res.push([i, data[i]])
		return res;
	}
	
	// setup control widget
	var updateInterval = 30;
	$("#updateInterval").val(updateInterval).change(function () {
		var v = $(this).val();
		if (v && !isNaN(+v)) {
			updateInterval = +v;
			if (updateInterval < 1)
				updateInterval = 1;
			if (updateInterval > 2000)
				updateInterval = 2000;
			$(this).val("" + updateInterval);
		}
	});
	
	if($("#serverLoad").length)
	{	
		var options = {
			series: { shadowSize: 1 },
			lines: { show: true, lineWidth: 3, fill: true, fillColor: { colors: [ { opacity: 0.9 }, { opacity: 0.9 } ] }},
			yaxis: { min: 0, max: 100, tickFormatter: function (v) { return v + "%"; }},
			xaxis: { show: false },
			colors: ["#FA5833"],
			grid: {	tickColor: "#f9f9f9",
					borderWidth: 0, 
			},
		};
		var plot = $.plot($("#serverLoad"), [ getRandomData() ], options);
		function update() {
			plot.setData([ getRandomData() ]);
			// since the axes don't change, we don't need to call plot.setupGrid()
			plot.draw();
			
			setTimeout(update, updateInterval);
		}

		update();
	}
	
});