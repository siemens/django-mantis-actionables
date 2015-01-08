

(function ($) {

    $(function() {


	require.config({
	    paths: {
		"datatables": "jquery.dataTables.min"
	    }
	});
	define('jquery', [], function() { return $; });
	require(['datatables'], function(){
	    var tables = {};
	    $.fn.dataTableExt.oStdClasses.sPaging = ' pull-right ' + $.fn.dataTableExt.oStdClasses.sPaging;
	    $.fn.dataTableExt.oStdClasses.sInfo = ' pull-left ' + $.fn.dataTableExt.oStdClasses.sInfo;

	    $.each($('.result_table'), function(i,v){
		var tbl = $(this);
		var tbl_key = $(this).attr('id');
		if(tbl_key == undefined || tbl_key == '')
		    return true;
		tables[tbl_key] = $(this).DataTable({
		    "processing": false,
		    "serverSide": true,
		    "stripeClasses": ["grp-row grp-row-odd", "grp-row grp-row-even"],
		    "order": [[0,"desc"]],
		    "ajax": {
			url: 'tbl_data',
			type: 'POST',
			data: {
			    "table_type": tbl_key
			},
			dataSrc: function(data){
			    // Fill the selectors
			    $.each($('tfoot select',tbl), function(i,v){
				var options = data.cols[$(v).attr('id')];
				if(options == undefined) return true;
				$.each(options, function(i1,v1){
				    $.each(v1, function(i2,v2){
					$(v).append($('<option></option>').text(v2).attr('value', v1[v2]));
				    });
				});
				// bind the change event
				$(this).on('change', function(e){
				    var colidx = $(this).parents('tr').first().children().index($(this).parent());
				    //dt.column(colidx).search($(this).val()).draw();
				    tables[tbl_key].column(colidx).search($(this).val()).draw();
				});
			    });

			    // Show total in headline
			    var hl_count = data.recordsTotal;
			    if(data.recordsFiltered != data.recordsTotal)
				hl_count = data.recordsFiltered + ' of ' + hl_count;
			    $(tbl).parents('.result_box').first().find('.res_num').first().text('('+hl_count+')');

			    return data.data;
			}
		    },
		    "createdRow": function ( row, data, index ) {
			$.each( $('thead tr', this).find('.tbl_hide'), function(i,v){
			    $('td', row).eq($(this).index()).addClass('tbl_hide');
			});


			//

			// Add cell class to those requiring it
			// if ( data[5].replace(/[\$,]/g, '') * 1 > 4000 ) {
			//     $('td', row).eq(5).addClass('highlight');
			// }
		    },
	    	    initComplete: function(settings, json) {
	    		var pthis = this;
			var s_cont = $('<div></div>').addClass('pull-right');
			var s_inp = $('<input type="text" placeholder="Filter">').keyup(function(){
			    var ithis = $(this);
			    window.clearTimeout($(this).data("timeout"));
			    $(this).data("timeout", setTimeout(function () {
				pthis.fnFilter(ithis.get(0).value);
			    }, 500));
	    	    	});
			var exp = $('<button>Export this data</button>').button({
			    icons: {
				primary: 'ui-icon-arrowthickstop-1-e'
			    },
			    text: false
			}).click(function(){
			    var params = pthis.oApi._fnAjaxParameters(pthis.dataTable().fnSettings());
			    params.table_type = tbl_key;
			    var qp = decodeURIComponent($.param(params));
			    var ifr = $('<iframe style="display:none;"></iframe>').attr('src', 'tbl_data_export?'+qp).appendTo($('body'));
			});
			var rst = $('<button>Reset filter</button>').button({
			    icons: {
				primary: 'ui-icon-close'
			    },
			    text: false
			}).addClass('dt_filter_rst').click(function(){
			    $(this).prev('input').val('').trigger('keyup');
			});
			var li = $('<span class="ui-icon ui-icon-clock tbl_processing pull-left" style="margin-top: 4px;display:none;"></span>');

			s_cont.append(li);
			s_cont.append(s_inp);
			s_cont.append(rst);
			s_cont.append(exp);

	    		$(this).parents('.result_box').first().find('.result_head').first().prepend(s_cont);

	    	    },
		    "drawCallback": function(settings){
	    		$(this).parents('.result_box').first().find('.paginate_button').button();
		    }
		}).on( 'processing.dt', function ( e, settings, processing ) {
		    var tpi = $(this).parents('.result_box').first().find('.tbl_processing').first();
		    tpi.css( 'display', processing ? 'block' : 'none' );
		} );
	    });



	});

    });
}(django.jQuery));
