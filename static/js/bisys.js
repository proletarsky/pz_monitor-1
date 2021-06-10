(function() {
  /**
   * Корректировка округления десятичных дробей.
   *
   * @param {String}  type  Тип корректировки.
   * @param {Number}  value Число.
   * @param {Integer} exp   Показатель степени (десятичный логарифм основания корректировки).
   * @returns {Number} Скорректированное значение.
   */
  function decimalAdjust(type, value, exp) {
    // Если степень не определена, либо равна нулю...
    if (typeof exp === 'undefined' || +exp === 0) {
      return Math[type](value);
    }
    value = +value;
    exp = +exp;
    // Если значение не является числом, либо степень не является целым числом...
    if (isNaN(value) || !(typeof exp === 'number' && exp % 1 === 0)) {
      return NaN;
    }
    // Сдвиг разрядов
    value = value.toString().split('e');
    value = Math[type](+(value[0] + 'e' + (value[1] ? (+value[1] - exp) : -exp)));
    // Обратный сдвиг
    value = value.toString().split('e');
    return +(value[0] + 'e' + (value[1] ? (+value[1] + exp) : exp));
  }

  // Десятичное округление к ближайшему
  if (!Math.round10) {
    Math.round10 = function(value, exp) {
      return decimalAdjust('round', value, exp);
    };
  }
  // Десятичное округление вниз
  if (!Math.floor10) {
    Math.floor10 = function(value, exp) {
      return decimalAdjust('floor', value, exp);
    };
  }
  // Десятичное округление вверх
  if (!Math.ceil10) {
    Math.ceil10 = function(value, exp) {
      return decimalAdjust('ceil', value, exp);
    };
  }
})();

'use strict'
class ChartsCreater{
  
  // ID РЅР°Р·РІР°РЅРёРµ РёР»Рё РѕР±СЉРµРєС‚, РІ РєРѕС‚РѕСЂС‹Р№ Р±СѓРґРµС‚ СЂР°Р·РјРµС‰С‘РЅС‹ РґРёР°РіСЂР°РјРјР°/РіСЂР°С„РёРє , json СЃ РїР°СЂР°РјРµС‚СЂР°РјРё
	constructor(chart_config){
		//this.chart_title = chart_title;
		this.chart_settings = [];
		this.chart_settings = chart_config;
		this.chart_title = 'РќР°Р·РІР°РЅРёРµ';
		this.ns = 'http://www.w3.org/2000/svg';	
		this.dataarray = this.chart_settings.dataset.data;
		this.datamax = this.chart_settings.dataset.data_max;
		
		
		// РѕР±СЉРµРєС‚ РёР»Рё id СЌР»РµРјРµРЅС‚Р°, РІ РєРѕС‚РѕСЂС‹Р№ Р±СѓРґРµС‚ РїРѕРјРµС‰С‘РЅ РіСЂР°С„РёРє
		//this.func(this.chart_settings.type);
	
		if (this.chart_settings.type){
			this.func_name = 'Create' + this.chart_settings.type;
			this.func_name_function = this['Create' + this.chart_settings.type];
			if('function' === typeof this.func_name_function) {
				switch(this.func_name){
					case 'CreateArachnidChart':
						return this.CreateArachnidChart();
						break;
					case 'CreatePieChart':
						return this.CreatePieChart();
						break;

					case 'CreateRoundChart':
						return this.CreateRoundChart();
						break;	
					default:
						break;
				}
			}
		}

	}

	// Р“РµРЅРµСЂРёСЂСѓРµС‚ СЃР»СѓС‡Р°Р№РЅРѕРµ С‡РёСЃР»Рѕ РІ РґРёР°РїР°Р·РѕРЅРµ РѕС‚ РґРѕ 
	getRandomInt(min,max){return Math.floor(Math.random() * (max - min)) + min;}

	//Data methods
	setDataSet(x){this.dataarray = x; }
	getDataSet(){return this.dataarray;}
	

	//Data methods
	setDataMaxSet(x){this.datamax = x; }
	getDataMaxSet(){return this.datamax[0];}

	//Math methods
	toRadians(degree){return degree * (Math.PI / 180);}
	toDegree(radians){return radians * (180 / Math.PI);}
	roundNumber(number, decimals){decimals = decimals || 3;return Math.round(number * Math.pow(10, decimals)) / Math.pow(10, decimals);}
	Msin(number){return this.roundNumber(Math.sin(this.toRadians(number)));}
	Mcos(number){return this.roundNumber(Math.cos(this.toRadians(number)));}
	Mtan(number){return this.roundNumber(Math.tan(this.toRadians(number)));}
	Masin(number){return this.roundNumber(this.toDegree(Math.asin(number)));}
	Macos(number){return this.roundNumber(this.toDegree(Math.acos(number)));}
	Matan(number){return this.roundNumber(this.toDegree(Math.atan(number)));}

	// РџРѕРґСЃС‚Р°РІР»СЏРµС‚ РЅР°Р·РІР°РЅРёРµ С„СѓРЅРєС†РёРё РёР· СЃС‚СЂРѕРєРё РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ
	func(key){
        key = this['Create' + key];
        if('function' === typeof key) {
            //return this.key(null,this.dataarray);
			self = this;
			return key(self);
			//return key();
        }
    }

// Charts methods  
// РџРѕСЃС‚СЂРѕРµРЅРёРµ РџР°СѓРєРѕРѕР±СЂР°Р·РЅРѕР№ РґРёР°РіСЂР°РјРјС‹  CreateArachnidChart( ['РџРѕРєР°Р·Р°С‚РµР»СЊ 1','РџРѕРєР°Р·Р°С‚РµР»СЊ 2', 'РџРѕРєР°Р·Р°С‚РµР»СЊ 3',...] , [53,30,12,...] );
  CreateArachnidChart(x){
	// labelsarray - РњР°СЃСЃРёРІ СЃ РЅР°Р·РІР°РЅРёСЏРјРё РїРѕРєР°Р·Р°С‚РµР»РµР№
	// dataarray - РњР°СЃСЃРёРІ СЃ РґР°РЅРЅС‹РјРё [12,13,22,56,3...] РјРѕР¶РµС‚ Р±С‹С‚СЊ С‚Р°РєРѕР№ [ [12,13,22,56,3...],[6,5,12,67,71...] ] РґР»СЏ РЅР°Р»РѕР¶РµРЅРёСЏ
	var dataarray = this.getDataSet();
	
	var padding=10,
		rgb1 = this.getRandomInt(0,255),
		rgb2 = this.getRandomInt(0,255),
		rgb3 = this.getRandomInt(0,255),		
		div = document.getElementById('arachnid-diagram'),
		svg = document.createElementNS(this.ns, 'svg'),
		g = document.createElementNS(this.ns, 'g');
		
		svg.classList.add('chart1');	
		svg.setAttributeNS(null, 'viewBox', '0 0 50 50');

		div.appendChild(svg);

	for (var i=1;i<=10;i++){
	var circle = document.createElementNS(this.ns, 'circle'),
		circle_margin=2,
		radius = i*circle_margin;
		
		circle.setAttributeNS(null, 'r', radius );
		circle.setAttributeNS(null, 'cx', '50%' );
		circle.setAttributeNS(null, 'cy', '50%' );
		circle.setAttributeNS(null, 'fill', 'transparent' );
		circle.setAttributeNS(null, 'stroke-width', '0.1' );
		circle.setAttributeNS(null,'stroke', '#5a5a5a' );
	
		svg.appendChild(circle);
	}
	
	var polyline_array = [ 
			['25,25,6.6,17.2'],
			['25,25,43.4,17.2'],
			['25,25,10,38.2'],
			['25,5,25,25'],
			['25,25,39.2,39.2'],
			['5,25,25,25'],
			['25,45,25,25'],
			['25,5,25,25'],
			['45,25,5,25'],
			['45,7.5,25,25'] 
		],
		polyline_string = '',
		polyline_numb = [],
		next_angel = 0,
		angels = 360;

	var start_fi = angels/(this.dataarray.length), new_start_fi;

	var self = this;
	this.dataarray.forEach(function(item, i, arr){
		polyline_array = [];		
		var r = 20;
		var fi = parseInt(i+1) * start_fi;

		if(start_fi<90 ){fi = parseInt(i+1) * start_fi - (270/arr.length);}
		if(start_fi<90 && (arr.length%2==0) ){fi = parseInt(i+1) * start_fi - (180/arr.length);}
		if(start_fi>90){fi = parseInt(i+1) * start_fi - (90/arr.length);}
		if(start_fi>=180 && start_fi<360){fi = parseInt(i+1) * start_fi - (180/arr.length);}
		if(start_fi>=360){fi = parseInt(i+1) * start_fi - (270/arr.length);}
		if(start_fi>90 && start_fi<180 && (arr.length%2!=0) ){fi = parseInt(i+1) * start_fi - (90/arr.length);}
		if(start_fi>90 && start_fi<180 && (arr.length%2==0) ){fi = parseInt(i+1) * start_fi - (180/arr.length);}
		
		var x = r * self.Mcos(fi);
		var y = r * self.Msin(fi);
				
		if( (x*(-1)) < 0 ){x = x + 25;}
		if( (x*(-1)) > 0 ){x = x + 25;}		
		if( (y*(-1)) < 0 ) {y = 25 - y;}
		if( (y*(-1)) > 0 ) {y = 25 + y*(-1);}				
		if( x==0 ){x=25;}
		if( y==0 ){y=25;}
		
		
		
		var circle_numb,
			step_cx,
			step_cy,
			circle_cx,
			circle_cy;
	
			if(x>25){
				step_cx = (x - 25)/10;
				circle_cx = 25 + ((item/10)*step_cx);
				}
				
			if(x<25){
				step_cx = (25 - x)/10; //1.5
				circle_cx =  30 - (5 + ((item/10)*step_cx)) ;
				}
				
			if(x==25){				
				circle_cx = 25;
				}
				
			//
			
			if(y>25){
				step_cy = (y - 25)/10;
				circle_cy = 25 + (item/10)*step_cy;
				}
								
			if(y==5){
				step_cy = 2;
				circle_cy = 5 + ((item/10)*step_cy);
			}
			
			if(y<25){
				step_cy = ( (25 - y) /10);
				circle_cy = (25 - (item/10)* step_cy);
				}
			
			if(y==25){circle_cy = 25;}
			
			//4 0 1 2 3
			circle_numb = parseInt(i+4);
			if( circle_numb >= arr.length ){
				circle_numb = circle_numb - parseInt(arr.length);
				}	
			polyline_array[i] = [25,25,x,y];
	
	
	var polyline = document.createElementNS(self.ns, 'polyline'); 
	
	polyline.setAttributeNS(null, 'x','25');
	polyline.setAttributeNS(null, 'y','25');
	polyline.setAttributeNS(null, 'stroke', '#000');
	polyline.setAttributeNS(null, 'stroke-width', '0.1');
	polyline.setAttributeNS(null, 'points', polyline_array[i]);
	polyline.setAttributeNS(null, 'viewBox', '0 0 50 50');
	polyline.setAttributeNS(null, 'fill', 'none');
	
	polyline_numb[circle_numb] = String(circle_cx)+','+String(circle_cy);
	
	
	var circle1 = document.createElementNS(self.ns, 'circle');	
	circle1.setAttributeNS(null, 'r', 0.1 );
	circle1.setAttributeNS(null, 'stroke-width', '0.2');
	circle1.setAttributeNS(null, 'cx', circle_cx );
	circle1.setAttributeNS(null, 'cy', circle_cy );
	circle1.setAttributeNS(null, 'fill', 'transparent' );
	circle1.setAttributeNS(null,'stroke', 'rgb('+55+', '+55+', '+55+')' );
	circle1.setAttributeNS(null,'data-value', item );
		
	g.appendChild(polyline);
	g.appendChild(circle1);
	
	
	
	});
	

for(var x=0;x<=polyline_numb.length-1;x++){	
	if (polyline_numb[x] !== undefined && polyline_numb[x].length > 0){
		polyline_string = polyline_string+' '+polyline_numb[x];
		if (x == polyline_numb.length-1){
			if (polyline_numb.length == 3){
				polyline_string = polyline_string+' '+'25,25';
			}
			polyline_string = polyline_string+' '+polyline_numb[0];
		}
	}
}
	
	var polyline1 = document.createElementNS(this.ns, 'polyline'); 
	///polyline1.setAttributeNS(null, 'class', 'fadein-block');
	polyline1.classList.add('fadein-block');
	polyline1.setAttributeNS(null, 'x', '25');
	polyline1.setAttributeNS(null, 'y', '25');
	polyline1.setAttributeNS(null, 'stroke', 'transparent');
	polyline1.setAttributeNS(null, 'stroke-width', '0');
	polyline1.setAttributeNS(null, 'points', polyline_string);
	polyline1.setAttributeNS(null, 'viewBox', '0 0 500 500');
	polyline1.setAttributeNS(null, 'fill', 'rgba(18 ,202, 25 , 0.7)');
	
	svg.appendChild(polyline1);
	svg.appendChild(g);
	
	for(var y=0;y<11;y++){
	var circle_cx = 23,
	circle_cy=25 - ((y)*2),
	text = document.createElementNS(this.ns, 'text');
	if(String(y*10).length==1){circle_cx = 23.5;}
	if(String(y*10).length==3){circle_cx = 22.5;}
	text.setAttributeNS(null, 'x', circle_cx);
	text.setAttributeNS(null, 'y', circle_cy);
	text.setAttributeNS(null, 'font-size', '1px');
	text.setAttributeNS(null, 'font-weight', 'bold');
	text.setAttributeNS(null, 'fill', '#000');
	text.setAttributeNS(null, 'letter-spacing', '0');
	text.textContent = y*10;
	
	svg.appendChild(text);
	}
	
}



CreatePieChart(x){
	var dashoffset = 0,
		arraysum = 0,
		array = this.getDataSet(),
		itemsProcessed=0;
		
	var ns = this.ns;
	var div1 = document.getElementById('drawing1');
	var svg1 = document.createElementNS(ns, 'svg');
	
	svg1.classList.add('chart');	
	svg1.setAttributeNS(null, 'viewBox', '0 0 50 50');
	
		
	var div = document.createElement('div'),
	ul = document.createElement('ul');
	
	div.classList.add('legend');
	ul.classList.add('caption-list');
		
	var self = this
// РўСѓС‚ РІС‹С‡РёСЃР»СЏРµРј СЃСѓРјРјСѓ РІСЃРµС… СЌР»РµРјРµРЅС‚РѕРІР° РІ РјР°СЃСЃРёРІРµ
	array.forEach(function(item, i, arr) {
	arraysum = arraysum + item[1];
	itemsProcessed++;
	
    if(itemsProcessed === arr.length){  
	  
	arr.forEach(function(item1, i1, arr1){
	var z = item1[1]; // Р­С‚Рѕ РїРѕРєР°Р·Р°С‚РµР»СЊ Р·РЅР°С‡РµРЅРёСЏ
	z = Math.ceil((100*z)/arraysum);
	//z = Math.ceil((100*z)/Math.ceil(arraysum));
	var li = document.createElement('li');
	var span = document.createElement('span');
	var rgb1 =self.getRandomInt(0,255) ,rgb2 = self.getRandomInt(0,255),rgb3 = self.getRandomInt(0,255);
	
	li.classList.add('caption-item');
	li.appendChild(span);
	span.style.background = 'rgb('+rgb1+', '+rgb2+', '+rgb3+')';
	if(item1[0]){
	li.innerHTML = li.innerHTML+' '+item1[0];
	}else{
		li.innerHTML = li.innerHTML+' Не указано';
	}
	
	ul.appendChild(li);
	
	
	var circle1 = document.createElementNS(ns, 'circle');
	circle1.classList.add('unit1');
	circle1.classList.add('fadein-block');
	circle1.setAttributeNS(null, 'r', 15.9 );
	circle1.setAttributeNS(null, 'cx', '50%' );
	circle1.setAttributeNS(null, 'cy', '50%' );
	circle1.setAttributeNS(null,'stroke', 'rgb('+rgb1+', '+rgb2+', '+rgb3+')' );
	var new_z=z;
	if(z==50){new_z=100;}
	circle1.setAttributeNS(null, 'stroke-dasharray', new_z +' 100');
	if(i1!=0){
	var y = Math.ceil(arr1[i1-1][1]);
	y = Math.ceil((100*y)/arraysum);
	dashoffset = Math.ceil(dashoffset + y);
	// circle1.setAttributeNS(null, 'stroke-dashoffset', -z - Math.ceil(arr1[i1-1][1]) ); dashoffset
	circle1.setAttributeNS(null, 'stroke-dashoffset', -dashoffset );
	}
	
	//Math.ceil()
	
	div.appendChild(ul);
	div1.appendChild(div);
	div1.appendChild(svg1);
	
	svg1.appendChild(circle1);
	
	});
	  
	  
	  
    }
});	
	
}



CreateRoundChart(){
	var dashoffset = 0,
		arraysum = 0,
		array = this.getDataSet(),
		datamax = this.getDataMaxSet(),
		itemsProcessed=0,
		rgb = new Array(),
		dont_selected = true;
		rgb.push('rgb(237, 192, 44)');
		rgb.push('rgb(195, 208, 160)');
		rgb.push('rgb(20, 195, 78)');
		rgb.push('rgb(57, 153, 125)');
		rgb.push('rgb(240, 7, 181)');
		rgb.push('rgb(132, 251, 158)');

	console.log(rgb);


		
	var ns = this.ns;
	var div1 = document.getElementById('drawing1');
	document.getElementById('drawing1').innerHTML='';
	var svg1 = document.createElementNS(ns, 'svg');
	
	svg1.classList.add('chart');	
	svg1.setAttributeNS(null, 'viewBox', '0 0 50 50');
	
		
	var div = document.createElement('div'),
	ul = document.createElement('ul');
	
	div.classList.add('legend');
	ul.classList.add('caption-list');
		
	var self = this;
// РўСѓС‚ РІС‹С‡РёСЃР»СЏРµРј СЃСѓРјРјСѓ РІСЃРµС… СЌР»РµРјРµРЅС‚РѕРІР° РІ РјР°СЃСЃРёРІРµ
	array.forEach(function(item, i, arr) {
	arraysum = parseInt(arraysum) + parseInt(item[1]);
	itemsProcessed++;
	
    if(itemsProcessed === arr.length){
	  
	arr.forEach(function(item1, i1, arr1){
	var z = item1[1]; // Р­С‚Рѕ РїРѕРєР°Р·Р°С‚РµР»СЊ Р·РЅР°С‡РµРЅРёСЏ
	//z = Math.ceil((100*z)/arraysum);
	console.log(z);
////	z = Math.round10( ((100*z)/arraysum),-1);
	z = Math.round10( ((100*z)/datamax),-1);
	//z = Math.ceil((100*z)/arraysum);
	if(!z){z=0;}
	//z = Math.ceil((100*z)/Math.ceil(arraysum));
	var li = document.createElement('li');
	var span = document.createElement('span');
	var rgb1 =self.getRandomInt(0,255) ,rgb2 = self.getRandomInt(0,255),rgb3 = self.getRandomInt(0,255);
	
	li.classList.add('caption-item');
	li.appendChild(span);
	//span.style.background = rgb[i1];
		if(item1[0]){
	span.style.background = rgb[i1];
	li.innerHTML = li.innerHTML+' '+item1[0]+' '+z+' %';
	}else{
		span.style.background = 'rgb('+236+', '+236+', '+236+')';
		li.innerHTML = li.innerHTML+' Не указано 100%';
	}
	//li.innerHTML = li.innerHTML+' '+item1[0]+' '+z+'%';
	
	ul.appendChild(li);
	
	
	var circle1 = document.createElementNS(ns, 'circle');
	circle1.classList.add('unit1');
	circle1.classList.add('fadein-block');
	circle1.setAttributeNS(null, 'r', 15.9 );
	circle1.setAttributeNS(null, 'cx', '50%' );
	circle1.setAttributeNS(null, 'cy', '50%' );
	circle1.setAttributeNS(null,'stroke', rgb[i1]);
	var new_z=z;
	if(z==50){new_z=100;}
	circle1.setAttributeNS(null, 'stroke-dasharray', new_z +' 100');
	if(i1!=0){
	var y = arr1[i1-1][1];
	y = ((100*y)/datamax);
	dashoffset = dashoffset + y;
	//Math.round
	//Math.ceil
	// circle1.setAttributeNS(null, 'stroke-dashoffset', -z - Math.ceil(arr1[i1-1][1]) ); dashoffset
	circle1.setAttributeNS(null, 'stroke-dashoffset', -dashoffset );
	}
	
	//Math.ceil()
	

	
	console.log('::::'+arraysum);
	if(arraysum<datamax && dont_selected ){
	var li1 = document.createElement('li'),
	 	span1 = document.createElement('span');
	 	
	li1.classList.add('caption-item');
	li1.appendChild(span);
	span.style.background = 'rgb('+236+', '+236+', '+236+')';
	span1.style.background = 'rgb(236, 236, 236)';
	li1.innerHTML = li1.innerHTML+'Не указано '+ ((100*(datamax-arraysum))/datamax)+' %';
	ul.appendChild(li1);
	dont_selected =false;
	}

	div.appendChild(ul);
	div1.appendChild(div);
	div1.appendChild(svg1);
	
	svg1.appendChild(circle1);
	
	});
	  
	  
	  
    }
});	
	
}


}