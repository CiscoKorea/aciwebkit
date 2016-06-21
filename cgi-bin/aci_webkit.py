#!/usr/bin/env python
#
# Written by Jacky Wang @ Cisco Systems, Mar 26 2015
# The script uses ACI Toolkit initially to create and 
# show apic/switch/ep/epg/contract/tenant info,
# as well as checking interface stats and more.
# Cobra and REST were used later to replace most ACI Toolkit
# code for better performance to handle large fabric with 20k+
# EPG and 100k+ EPs.
# DataTables with Bootstrap extension is used to present data.


# list of packages that should be imported for this code to work
from acitoolkit.acitoolkit import *
from acitoolkit.aciphysobject import *
from acitoolkit.aciConcreteLib import ConcreteAccCtrlRule
import re
import sys
import cgi
import os
import base64
import urllib
import json
import requests
from quik import Template   # A fast and lightweight Python template engine
import subprocess, glob, shutil, tempfile
from natsort import natsorted   # sort based on natural language

try:
    import requests.packages.urllib3
    requests.packages.urllib3.disable_warnings()
except:
    pass

# enable debugging
import cgitb; cgitb.enable()

# get self URL
if os.environ['REQUEST_METHOD'] == 'GET':
    URL = os.environ['HTTP_HOST'] + os.environ['REQUEST_URI']
elif os.environ['REQUEST_METHOD'] == 'POST':
    URL = os.environ['HTTP_REFERER'][7:]


def print_html_header():
    # source css for dashboard
    if re.match(r'.*&pname.*', URL):
        dashboard_css = ''
    else:
        dashboard_css = '<link href="/src/style.min.css" rel="stylesheet">'
    # source css/javascript for DualListbox
    if 'flip_port' in URL or 'delete_tn' in URL:
        DualListbox_script = '<script src="/src/jquery.bootstrap-duallistbox.js"></script>\
                              <link rel="stylesheet" type="text/css" href="/src/bootstrap-duallistbox.css">'
    else:
        DualListbox_script = ''
    # source css/javascript for jasny file input and mergely diff
    if 'xml_diff' in URL:
        jasny_script = '<script src="/src/jasny-bootstrap.min.js"></script>\
                        <link href="/src/jasny-bootstrap.min.css" rel="stylesheet">'
        mergely_script = '<!-- Requires CodeMirror 2.16 -->\
                        <script type="text/javascript" src="/src/codemirror.js"></script>\
                        <script type="text/javascript" src="/src/xml.js"></script>\
                        <link type="text/css" rel="stylesheet" href="/src/codemirror.css" />\
                        <!-- Requires Mergely -->\
                        <script type="text/javascript" src="/src/mergely.js"></script>\
                        <link type="text/css" rel="stylesheet" href="/src/mergely.css" />'
    else:
        jasny_script = ''
        mergely_script = ''
    # list of menu items need spinner
    ids = ['delete_tn',
           'show_dashboard',
           'show_apic', 
           'show_switch', 
           'show_ctrct', 
           'show_ctrct_detail', 
           'show_ep', 
           'show_epg', 
           'show_instP', 
           'show_rule', 
           'show_subnet', 
           'show_tenant',
           'stat_intf',
           'find_dup_ip',
           'flip_port',
           'xml_diff']
    temp = Template("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ACI Webkit</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="icon" type="image/png" href="/favicon.png"/>
        <!-- start: customized stylesheet with navbar-brand -->
        @dashboard_css
        <!-- end: customized stylesheet -->
        <link rel="stylesheet" href="/src/bootstrap.min.css">
        <!-- <link rel="stylesheet" href="/src/dataTables.bootstrap.css"> -->
        <link rel="stylesheet" href="/src/dataTables.bootstrap.css">
        <link rel="stylesheet" href="/src/buttons.dataTables.min.css">
        <script src="/src/jquery-1.12.0.min.js"></script>
        <script src="/src/jquery.dataTables.min.js"></script>
        <script src="/src/dataTables.buttons.min.js"></script>
        <script src="/src/dataTables.bootstrap.js"></script>
        <script src="/src/jszip.min.js"></script>
        <script src="/src/buttons.html5.min.js"></script>
        <script src="/src/natural.js"></script>
        <script src="/src/bootstrap.min.js"></script>
        <script type="text/javascript" src="/src/spin.min.js"></script>
        <!-- start: stylesheet/javascript for DualListbox -->
        @DualListbox_script
        <!-- end: stylesheet/javascript for DualListbox -->
        <!-- CSS to style the jasny file input field as button -->
        @jasny_script
        <!-- CSS to style the mergely file diff -->
        @mergely_script
        <!-- stylesheet for bs3 dropdown submenu -->
        <link rel="stylesheet" href="/src/bs3_submenu.css">
        <script type="text/javascript">
        $(document).ready( function () {
            $('#tooltip_back').tooltip();
            $('#tooltip_refresh').tooltip();
            $('#tooltip_exit').tooltip();
            $('#tooltip_about').tooltip();
        } );
        </script>
        <!-- script for spinner -->
        <script>
        var opts = {
          lines: 11,
          length: 22,
          width: 12,
          radius: 30,
          scale: 0.75,
          corners: 1,
          rotate: 0,
          direction: 1,
          color: '#000',
          speed: 0.6,
          trail: 60,
          shadow: false,
          hwaccel: false,
          className: 'spinner',
          zIndex: 2e9,
          top: 'auto',
          left: 'auto'
        };
        var spinner = null;
        var spinner_div = 0;
        $(document).ready(function() {
            spinner_div = $('#spinner').get(0);
            $('#tooltip_refresh').on('click', function(e) {
                if(spinner == null) {
                  spinner = new Spinner(opts).spin(document.getElementById('spinner'));
                } else {
                  spinner.spin(spinner_div);
                }
            });            
            #for @id in @ids:
                $('#nid_@id').on('click', function(e) {
                    if(spinner == null) {
                      spinner = new Spinner(opts).spin(document.getElementById('spinner'));
                    } else {
                      spinner.spin(spinner_div);
                    }
                });
            #end
        });
        </script>
        <!-- end: spinner -->
        <!-- start: Dashboard theme - http://bootstrapmaster.com/demo/simpliq/ -->
        <script src="/src/jquery.knob.modified.min.js"></script>
        <script src="/src/core.min.js"></script>
        <script src="/src/page-infrastructure.js"></script>
        <!-- <script src="/src/page-infrastructure.js"></script> -->
        <script src="/src/jquery-migrate-1.2.1.min.js"></script>
        <!-- end: Dashboard theme -->
        <!-- script for bs3 submenu -->
        <script>
        (function($){
            $(document).ready(function(){
                $('ul.dropdown-menu [data-toggle=dropdown]').on('click', function(event) {
                    event.preventDefault(); 
                    event.stopPropagation(); 
                    $(this).parent().siblings().removeClass('open');
                    $(this).parent().toggleClass('open');
                });
            });
        })(jQuery);
        </script>
        <!-- end script for bs3 submenu -->        
    </head>
    <body>
    """)
    print temp.render(locals())


def print_navbar(aip, usr, pwd):
    base_url = 'http://' + re.sub(r'&pname.*$', "", URL)
    home_url = 'http://' + os.environ['HTTP_HOST'] + '/aci_webkit.html'
    temp = Template("""
    <nav class="navbar navbar-inverse navbar-fixed-top">
      <div class="container-fluid">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#myNavbar">
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>                        
          </button>
          <a id="nid_show_dashboard" class="navbar-brand" href="@base_url"><img src="/src/sk-hynix-logo.png" width="50px" heigth="50px"/>ACI Webkit</a>
        </div>
        <div class="collapse navbar-collapse" id="myNavbar">
          <ul class="nav navbar-nav">
            <li class="dropdown">
              <a class="dropdown-toggle" data-toggle="dropdown" href=" "><span class="glyphicon glyphicon-sunglasses"></span> Show <span class="caret"></span></a>
              <ul class="dropdown-menu">
                <li><a id="nid_show_apic" href="@base_url&pname=show_apic">APIC</a></li>
                <li><a id="nid_show_switch" href="@base_url&pname=show_switch">Switch</a></li>
                <li class="divider"></li>
                <li class="dropdown dropdown-submenu">
                    <a href="#" class="dropdown-toggle" data-toggle="dropdown">Contract</a>
                    <ul class="dropdown-menu">
                        <li><a id="nid_show_ctrct" href="@base_url&pname=show_ctrct">Brief</a></li>
                        <li><a id="nid_show_ctrct_detail" href="@base_url&pname=show_ctrct_detail">Detail</a></li>
                    </ul>
                </li>
                <li><a id="nid_show_ep" href="@base_url&pname=show_ep">End Point</a></li>
                <li><a id="nid_show_epg" href="@base_url&pname=show_epg">End Point Group</a></li>
                <li><a id="nid_show_instP" href="@base_url&pname=show_instP">L3 External Network</a></li>
                <li><a id="nid_show_rule" href="@base_url&pname=show_rule">Rule</a></li>
                <li><a id="nid_show_subnet" href="@base_url&pname=show_subnet">Subnet</a></li>
                <li><a id="nid_show_tenant" href="@base_url&pname=show_tenant">Tenant</a></li>
              </ul>
            </li>
            <li class="dropdown">
              <a class="dropdown-toggle" data-toggle="dropdown" href=" "><span class="glyphicon glyphicon-signal"></span> Stats <span class="caret"></span></a>
               <ul class="dropdown-menu">
                <li><a id="nid_stat_intf" href="@base_url&pname=stat_intf">Interface Utilization</a></li>
               </ul>
            </li>
            <li class="dropdown">
              <a class="dropdown-toggle" data-toggle="dropdown" href=" "><span class="glyphicon glyphicon-wrench"></span> Tools <span class="caret"></span></a>
               <ul class="dropdown-menu">
                <li><a id="nid_find_dup_ip" href="@base_url&pname=find_dup_ip">Find EP with Dup IP</a></li>
                <li><a href="http://ecats-wiki/Templatized_APIC_Configurator" target="_blank">Template Configurator</a></li>
                <li><a id="nid_xml_diff" href="@base_url&pname=xml_diff">XML diff</a></li>
               </ul>
            </li>
          </ul>
          <ul class="nav navbar-nav navbar-right">
            <li><a href="javascript:javascript:history.go(-1)" title="Back" data-placement="bottom" id="tooltip_back"><span class="glyphicon glyphicon-arrow-left"></span> </a></li>
            <li><a href="javascript:location.reload(true)" title="Refresh" data-placement="bottom" id="tooltip_refresh"><span class="glyphicon glyphicon-refresh"></span> </a></li>
            <li><a href="@home_url" title="Exit" data-placement="bottom" id="tooltip_exit"><span class="glyphicon glyphicon-log-out"></span> </a></li>
            <li><a data-toggle="modal" data-target="#myModal" title="About" data-placement="bottom" id="tooltip_about"><span class="glyphicon glyphicon-info-sign"></span> </a></li>
          </ul>
        </div>
      </div>
    </nav><br><br><br>
    <!-- Modal -->
    <div id="myModal" class="modal fade" role="dialog">
      <div class="modal-dialog">
        <!-- Modal content-->
        <div class="modal-content">
          <div class="modal-header">
            <button type="button" class="close" data-dismiss="modal">&times;</button>
            <h3 class="modal-title"><b>ACI Webkit</b></h3>
          </div>
          <div class="modal-body">
            <h4><b>About</b></h4>
            <p>The tool was initially created to demo the ACI programmability (Cobra) in customer POC visits. 
            Then I re-wrote it using ACItoolkit (with local mods) for learning purpose. And eventually moved to
            REST for better performance and scalability. More features were added along the way to make managing
            and trouble-shooting ACI easier. The frontend UI was tested on Windows/Chrome only, and backend
            runs on my Ubuntu VM, so the performance could be slow sometimes.</p>
            <h4><b>Features</b></h4>
            <li>Bulk add/delete tenants</li>
            <li>Show fabric (APIC|Switch), and EP|EPG|L3Out|Subnet|Tenant info</li>
            <li>Show brief|detail contract consumer/provider info</li>
            <li>Show TCAM rules with scope/pctag/filtId resloved to actual Context/EPG/Filter names</li>
            <li>Show active interface utilization(%)</li>
            <li>Find Endpoints with duplicate IP</li>
            <li>Port flipper to flip bulk number of ports at random intervals</li>
            <li>XML diff tool to compare ACI configs, and more...</li>
            <h4><b>Support</b></h4>
            <p>Best effort. If you run into any issues, or have any comments, please feel free to drop me a <a href="mailto:xiangrow@cisco.com" target="_top">line</a>.</p>
            <p>Thanks/Jacky</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-primary" data-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
    <div class="container-fluid">
    """)
    print temp.render(locals())
    # spinner div
    print '<div id="spinner" style="position:fixed;top:50%;left:50%;z-index:1000"></div>'


def print_data_table(fname, type=None):
    if type == 'hide_first_col':
        columnDefs = ', {"targets": [ 0 ], "visible": false, "searchable": false}'
    else:
        columnDefs = ''
    temp = Template("""
    <script type="text/javascript">
    var table;
    $(document).ready( function () {
        table = $('#table_id').DataTable( {
            "ajax": "@fname",
            "deferRender": true,
            columnDefs: [
              { type: 'natural', targets: 0 }
              @columnDefs
            ],
            dom: 'Bfrtip',
            lengthMenu: [
                [ 10, 25, 50, -1 ],
                [ '10 rows', '25 rows', '50 rows', 'Show all' ]
            ],
            buttons: [
                'pageLength',
                'excelHtml5',
                'csvHtml5'
            ],
            search: {
                "regex": false
            }
        } );
    } );
    </script>
    """)
    print temp.render(locals())


def save_table_data(data):
    tempfile.tempdir = '/var/www/html/tmp'
    outfile = tempfile.NamedTemporaryFile(delete=False)
    try:
        json.dump(data, outfile)
        return outfile.name.split('/var/www/html')[1]
    finally:
        outfile.close()


def spinner(ids=[], action='hide'):
    spinner_show = Template("""
        <script>
        $(document).ready(function() {
            spinner_div = $('#spinner').get(0);
            #for @id in @ids:
                $("#nid_@id").on('click', function(e) {
                    if(spinner == null) {
                      spinner = new Spinner(opts).spin(document.getElementById('spinner'));
                    } else {
                      spinner.spin(spinner_div);
                    }
                });
            #end
        });
        </script>
    """)
    spinner_hide = Template("""
        <script>
            $(window).load(function() {
             // executes when complete page is fully loaded, including all frames, objects and images
             spinner.stop(spinner_div);
            });
        </script>
    """)
    if action == 'show':
        print spinner_show.render(locals())
    else:
        print spinner_hide.render(locals())


def rest_login(APIC, USER, PASS):
    """login apic with rest

    Args:
        APIC: apic ip
        USER: apic user name
        PASS: apic password

    Returns:
        rest response
    """

    auth = {
        'aaaUser': {
            'attributes': {
                'name': USER,
                'pwd': PASS
                }
            }
        }
    url = 'https://{}/api/aaaLogin.json'.format(APIC)
    resp = requests.post(url, data=json.dumps(auth), timeout=1800, verify=False)
    return resp


def get_json(rest, path):
    """get json from apic

    Args:
        rest: apic request login response
        path: request URL, e.g. 'api/class/fvCEp.json?rsp-subtree-include=count'

    Returns:
        Json data
    """
    cookies = rest.cookies
    url = rest.url.split('/api/')[0] + path
    resp = requests.get(url, cookies=cookies, verify=False)
    if resp.status_code == requests.codes.ok:
        return json.loads(resp.text)
    else:
        return False


def get_json_helper(args):
  # auxiliary funciton of get_json for parallel processing
  return get_json(*args)['imdata']


def get_json_parallel(rest, pc, ps, url):
  from multiprocessing.dummy import Pool as ThreadPool
  import itertools
  job_args = []
  for p in range(pc):
    job_args.append((rest, '{}&page={}&page-size={}'.format(url, p, ps)))
  pool = ThreadPool(pc) 
  results = pool.map(get_json_helper, job_args)
  #close the pool and wait for the work to finish 
  pool.close() 
  pool.join() 
  return list(itertools.chain.from_iterable(results))


def get_page_info(rest, cls):
    psize = 80000
    count = int(get_json(rest, '/api/class/{}.json?rsp-subtree-include=count'.format(cls))['imdata'][0]['moCount']['attributes']['count'])
    if count > psize:
        return(count / psize + 1, psize)
    return(1, psize)


def get_timestamp():
    import time
    import datetime
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%m/%d/%y %H:%M:%S.%f')
    return st


def interface_disable(session, interface, tDn):
    url = '/api/node/mo/uni/fabric/outofsvc.json'
    payload = [{'fabricRsOosPath': {'attributes': {'tDn': tDn, 'lc': 'blacklist'}, 'children': []}}]
    resp = session.push_to_apic(url, payload)
    print '[%s]: %s is ' % (get_timestamp(), interface[0].name)
    if not resp.ok:
        print '%% Error: Could not push configuration to APIC'
        print resp.text
    else:
        print 'down<br>'


def interface_enable(session, interface, tDn):
    url = '/api/node/mo/uni/fabric/outofsvc.json'
    dn = "uni/fabric/outofsvc/rsoosPath-[{}]".format(tDn)
    payload = [{'fabricRsOosPath': {'attributes': {'dn': dn, 'status': 'deleted'}, 'children': []}}]
    resp = session.push_to_apic(url, payload)
    print '[%s]: %s is ' % (get_timestamp(), interface[0].name)
    if not resp.ok:
        print '%% Error: Could not push configuration to APIC'
        print resp.text
    else:
        print 'up<br>'


def show_dashboard(rest):
    fvTenant_max = 64000
    fvBD_max = 15000
    fvAEPg_max = 15000
    fvCEp_max = 180000
    vzFilter_max = 10000
    vzBrCP_max = 1000
    vnsCDev_max = 1200
    vnsGraphInst_max = 600
    fvTenant_cnt = get_json(rest, '/api/class/fvTenant.json?rsp-subtree-include=count')['imdata'][0]['moCount']['attributes']['count']
    fvBD_cnt = get_json(rest, '/api/class/fvBD.json?rsp-subtree-include=count')['imdata'][0]['moCount']['attributes']['count']
    fvAEPg_cnt = get_json(rest, '/api/class/fvAEPg.json?rsp-subtree-include=count')['imdata'][0]['moCount']['attributes']['count']
    fvCEp_cnt = get_json(rest, '/api/class/fvCEp.json?rsp-subtree-include=count')['imdata'][0]['moCount']['attributes']['count']
    vzFilter_cnt = get_json(rest, '/api/class/vzFilter.json?rsp-subtree-include=count')['imdata'][0]['moCount']['attributes']['count']
    vzBrCP_cnt = get_json(rest, '/api/class/vzBrCP.json?rsp-subtree-include=count')['imdata'][0]['moCount']['attributes']['count']
    vnsCDev_cnt = get_json(rest, '/api/class/vnsCDev.json?rsp-subtree-include=count')['imdata'][0]['moCount']['attributes']['count']
    vnsGraphInst_cnt = get_json(rest, '/api/class/vnsGraphInst.json?rsp-subtree-include=count')['imdata'][0]['moCount']['attributes']['count']
    fvTenant_pct = int(round(float(fvTenant_cnt) / fvTenant_max * 100))
    fvBD_pct = int(round(float(fvBD_cnt) / fvBD_max * 100))
    fvAEPg_pct = int(round(float(fvAEPg_cnt) / fvAEPg_max * 100))
    fvCEp_pct = int(round(float(fvCEp_cnt) / fvCEp_max * 100))
    vzFilter_pct = int(round(float(vzFilter_cnt) / vzFilter_max * 100))
    vzBrCP_pct = int(round(float(vzBrCP_cnt) / vzBrCP_max * 100))
    vnsCDev_pct = int(round(float(vnsCDev_cnt) / vnsCDev_max * 100))
    vnsGraphInst_pct = int(round(float(vnsGraphInst_cnt) / vnsGraphInst_max * 100))
    temp = Template("""
    <h2>Dashboard</h2>
    <div class="circleStats row hideInIE8">
        <div class="col-md-3 col-sm-4 col-xs-6">
            <div class="circleStatsItemBox">
                <div class="header">Tenants</div>
                <div class="circleStat">
                    <input type="text" value="@fvTenant_pct" class="orangeCircle" />
                </div>
                <span class="countpanel">@fvTenant_cnt</span>
                <div class="footer">
                    <span class="count">
                        <span class="number">@fvTenant_cnt</span>
                        <span class="unit"></span>
                    </span>
                    <span class="sep"> / </span>
                    <span class="value">
                        <span class="number">@fvTenant_max</span>
                        <span class="unit"></span>
                    </span> 
                </div>
            </div>
        </div><!--/col-->
        <div class="col-md-3 col-sm-4 col-xs-6">
            <div class="circleStatsItemBox">
                <div class="header">Bridge Domains</div>
                <div class="circleStat">
                    <input type="text" value="@fvBD_pct" class="orangeCircle" />
                </div>
                <span class="countpanel">@fvBD_cnt</span>
                <div class="footer">
                    <span class="count">
                        <span class="number">@fvBD_cnt</span>
                        <span class="unit"></span>
                    </span>
                    <span class="sep"> / </span>
                    <span class="value">
                        <span class="number">@fvBD_max</span>
                        <span class="unit"></span>
                    </span> 
                </div>
            </div>
        </div><!--/col-->
        <div class="col-md-3 col-sm-4 col-xs-6">
            <div class="circleStatsItemBox">
                <div class="header">Endpoint Groups</div>
                <div class="circleStat">
                    <input type="text" value="@fvAEPg_pct" class="orangeCircle" />
                </div>
                <span class="countpanel">@fvAEPg_cnt</span>
                <div class="footer">
                    <span class="count">
                        <span class="number">@fvAEPg_cnt</span>
                        <span class="unit"></span>
                    </span>
                    <span class="sep"> / </span>
                    <span class="value">
                        <span class="number">@fvAEPg_max</span>
                        <span class="unit"></span>
                    </span> 
                </div>
            </div>
        </div><!--/col-->
        <div class="col-md-3 col-sm-4 col-xs-6 noMargin">
            <div class="circleStatsItemBox">
                <div class="header">Endpoints</div>
                <div class="circleStat">
                    <input type="text" value="@fvCEp_pct" class="orangeCircle" />
                </div>
                <span class="countpanel">@fvCEp_cnt</span>
                <div class="footer">
                    <span class="count">
                        <span class="number">@fvCEp_cnt</span>
                        <span class="unit"></span>
                    </span>
                    <span class="sep"> / </span>
                    <span class="value">
                        <span class="number">@fvCEp_max</span>
                        <span class="unit"></span>
                    </span> 
                </div>
            </div>
        </div><!--/col-->
        <div class="col-md-3 col-sm-4 col-xs-6">
            <div class="circleStatsItemBox">
                <div class="header">Filters</div>
                <div class="circleStat">
                    <input type="text" value="@vzFilter_pct" class="orangeCircle" />
                </div>
                <span class="countpanel">@vzFilter_cnt</span>      
                <div class="footer">
                    <span class="count">
                        <span class="number">@vzFilter_cnt</span>
                        <span class="unit"></span>
                    </span>
                    <span class="sep"> / </span>
                    <span class="value">
                        <span class="number">@vzFilter_max</span>
                        <span class="unit"></span>
                    </span> 
                </div>
            </div>
        </div><!--/col-->
        <div class="col-md-3 col-sm-4 col-xs-6">
            <div class="circleStatsItemBox">
                <div class="header">Contracts</div>
                <div class="circleStat">
                    <input type="text" value="@vzBrCP_pct" class="orangeCircle" />
                </div>
                <span class="countpanel">@vzBrCP_cnt</span>
                <div class="footer">
                    <span class="count">
                        <span class="number">@vzBrCP_cnt</span>
                        <span class="unit"></span>
                    </span>
                    <span class="sep"> / </span>
                    <span class="value">
                        <span class="number">@vzBrCP_max</span>
                        <span class="unit"></span>
                    </span> 
                </div>
            </div>
        </div><!--/col-->
        <div class="col-md-3 col-sm-4 col-xs-6">
            <div class="circleStatsItemBox">
                <div class="header">L4/L7 Devices</div>
                <div class="circleStat">
                    <input type="text" value="@vnsCDev_pct" class="orangeCircle" />
                </div>
                <span class="countpanel">@vnsCDev_cnt</span>
                <div class="footer">
                    <span class="count">
                        <span class="number">@vnsCDev_cnt</span>
                        <span class="unit"></span>
                    </span>
                    <span class="sep"> / </span>
                    <span class="value">
                        <span class="number">@vnsCDev_max</span>
                        <span class="unit"></span>
                    </span> 
                </div>
            </div>
        </div><!--/col-->
        <div class="col-md-3 col-sm-4 col-xs-6 noMargin">
            <div class="circleStatsItemBox">
                <div class="header">L4/L7 Graphs</div>
                <div class="circleStat">
                    <input type="text" value="@vnsGraphInst_pct" class="orangeCircle" />
                </div>
                <span class="countpanel">@vnsGraphInst_cnt</span>
                <div class="footer">
                    <span class="count">
                        <span class="number">@vnsGraphInst_cnt</span>
                        <span class="unit"></span>
                    </span>
                    <span class="sep"> / </span>
                    <span class="value">
                        <span class="number">@vnsGraphInst_max</span>
                        <span class="unit"></span>
                    </span> 
                </div>
            </div>
        </div><!--/col-->
    </div><!--/row-->   
    """)
    print temp.render(locals())


def config_tn(session, tn_name):
    print 'Configuring Tenant: <b>%s</b>...' % tn_name
    # Create the Tenant
    tenant = Tenant(tn_name)
    # Push it all to the APIC
    resp = session.push_to_apic(tenant.get_url(), tenant.get_json())
    if not resp.ok:
        print '%% Error: Could not push configuration to APIC'
        print resp.text
    else:
        print 'success<br>'


def generate_page_common(heading):
    url = 'http://' + URL
    action_url = url.split('?')[0]
    param = []
    for pair in url.split('?')[1].split('&'):
        name, value = pair.split('=')
        list = []
        list.append(name)
        list.append(urllib.unquote(value).decode('utf8'))
        param.append(list)
    temp = Template("""
    <div class="col-md-6">
      <div class="panel panel-info">
        <div class="panel-heading">@heading</div>
        <div class="panel-body">
            <form class="form-horizontal" role="form" action="@action_url" method="get">
    """)
    print temp.render(locals())
    for param_name, param_value in param:
        print '<input type=\"hidden\" class=\"form-control\" name=\"%s\" value=\"%s\">' % (param_name, param_value)


def create_tn(session):
    form = cgi.FieldStorage()
    if form.getfirst("action") == '1':     # Create tenant(s)
        print '''
        <div class="col-md-6">
          <div class="panel panel-info">
            <div class="panel-heading">Create Tenant</div>
            <div class="panel-body">
        '''
        if form.getfirst("tn_name") != None:
            if form.getfirst("start") == None or form.getfirst("count") == None:    # one tenant
                if form.getfirst("sfx") == None:
                    tn_name = form.getfirst("tn_name")
                else:
                    tn_name = form.getfirst("tn_name") + form.getfirst("con", '') + form.getfirst("sfx", '')
                config_tn(session, tn_name)
                print 'Done'
            else:   # multiple tenant
                count = int(form.getfirst("count"))
                start = int(form.getfirst("start"))
                step = int(form.getfirst("step", 1))
                for i in range(0, count):
                    id = str(start + step * i)
                    if form.getfirst("sfx") == None:
                        tn_name = form.getfirst("tn_name") + form.getfirst("con", '') + id
                    else:
                        tn_name = form.getfirst("tn_name") + form.getfirst("con", '') + id + form.getfirst("con", '') + form.getfirst("sfx", '')
                    config_tn(session, tn_name)
                print 'Done'
        else:
            print '<span class=\"glyphicon glyphicon-remove-circle\" aria-hidden=\"true\"  style=\"font-size:2em; color:red\"></span> Tenant name can not be Null.'
        print '</div></div></div></div>'
    else:   # Show config tenant page
        generate_page_common('Configure Tenant')
        print '''   
                  <div class="form-group">
                    <label class="col-sm-2 control-label">Tenant Name</label>
                    <div class="col-sm-9">
                      <input type="text" class="form-control" name="tn_name" placeholder="Required">
                      <p class="help-block">Tenant name for one tenant or common name for multiple tenants</p>
                    </div>
                  </div>

                  <div class="form-group">
                    <label class="col-sm-2 control-label">Start</label>
                    <div class="col-sm-9">
                      <input type="number" class="form-control" name="start" placeholder="Optional">
                      <p class="help-block">First tenant number when creating multiple tenants</p>
                    </div>
                  </div>
                 
                  <div class="form-group">
                    <label class="col-sm-2 control-label">Count</label>
                    <div class="col-sm-9">
                      <input type="number" class="form-control" name="count" placeholder="Optional">
                      <p class="help-block">Total tenants to create</p>
                    </div>
                  </div>

                  <div class="form-group">
                    <label class="col-sm-2 control-label">Step</label>
                    <div class="col-sm-9">
                      <input type="number" class="form-control" name="step" placeholder="Optional. Default is 1.">
                      <p class="help-block">The amount by which the start counter is incremented each time</p>
                    </div>
                  </div>

                  <div class="form-group">
                    <label class="col-sm-2 control-label">Suffix</label>
                    <div class="col-sm-9">
                      <input type="text" class="form-control" name="sfx" placeholder="Optional">
                      <p class="help-block">String to be appended at the end of tenant name</p>
                    </div>
                  </div>

                  <div class="form-group">
                    <label class="col-sm-2 control-label">Seperator</label>
                    <div class="col-sm-9">
                      <select class="form-control" name="con">
                        <option value="">Null</option>
                        <option value="-">Hyphen '-'</option>
                        <option value="_" selected>Underline '_'</option>
                        <option value=".">Dot '.'</option>
                      </select>
                      <p class="help-block">Seperator to concat tenant name with counter and suffix, e.g. 'tenant_counter_suffix'</p>
                    </div>
                  </div>
                  <input type="hidden" class="form-control" name="action" value="1">
                  <div class="col-sm-12">
                    <button type="submit" class="btn btn-primary pull-right">Create</button>
                  </div>
                </form>
            </div>
          </div>
        </div>
        '''


def delete_tn(rest, session):
    form = cgi.FieldStorage()
    if form.getfirst("action") == '1':     # Delete tenant
        print '''
        <div class="col-md-6">
          <div class="panel panel-info">
            <div class="panel-heading">Delete Tenant</div>
            <div class="panel-body">
        '''
        if form.getlist("tns"):
            all_tn = {}
            for tmp_tn in Tenant.get(session):
                all_tn[tmp_tn.name] = tmp_tn
            for tn in form.getlist("tns"):
                print 'Deleting Tenant: <b>%s</b>...' % tn
                all_tn[tn].mark_as_deleted()
                resp = session.push_to_apic(all_tn[tn].get_url(), data=all_tn[tn].get_json())
                if not resp.ok:
                    print '%% Error: Could not push configuration to APIC'
                    print resp.text
                else:
                    print 'success<br>'
            print 'Done'
        else:
            print '<span class=\"glyphicon glyphicon-remove-circle\" aria-hidden=\"true\"  style=\"font-size:2em; color:red\"></span> Tenant list can not be Null.'
        print '</div></div></div></div>'
    else:   # Show delete tenant page
        generate_page_common('Delete Tenant')
        # Get all tenants
        tns = []
        for fvTenant in get_json(rest, '/api/class/fvTenant.json?rsp-prop-include=naming-only')['imdata']:
            tns.append(fvTenant['fvTenant']['attributes']['name'])
        tns = natsorted(tns)
        temp = Template("""
          <div class="form-group">
            <div class="col-sm-12">
              <select multiple="multiple" size="10" name="tns">
                #for @tn in @tns:
                  <option value="@tn">@tn</option>
                #end
              </select>
            </div>
          </div>
          <input type="hidden" class="form-control" name="action" value="1">
          <div class="col-sm-12">
            <button type="submit" class="btn btn-primary pull-right" onclick="return confirm('Are you sure you want to delete the tenants?')">Delete</button>
          </div>
         </form>
            <script>
            var flipper = $('select[name="tns"]').bootstrapDualListbox({
              nonSelectedListLabel: 'Available Tenants',
              selectedListLabel: 'Selected Tenants',
              preserveSelectionOnMove: 'moved',
              moveOnSelect: false,
              helperSelectNamePostfix: ''
            });
            </script>
         </div>
         </div>
        </div>
        """)
        print temp.render(locals())


def show_apic(md):
    # Print the APIC list
    print '<h2>APIC List</h2>'
    # print APIC table header
    print '''
    <table id="table_id" class="table table-striped table-bordered" cellspacing="0" width="100%">
        <thead>
            <tr>
                <th>Id</th>
                <th>Name</th>
                <th>Role</th>
                <th>Model</th>
                <th>Serial</th>
                <th>Version</th>
                <th>INB Mgmt IP</th>
                <th>OOB Mgmt IP</th>
                <th>State</th>
                <th>System Uptime</th>
            </tr>
        </thead>
    </table>
    '''
    # populate with model info
    fabricNode_model_list = {}
    fabricNode_list = md.lookupByClass('fabricNode', propFilter='eq(fabricNode.role,"controller")')
    for fabricNode in fabricNode_list:
        fabricNode_model_list[fabricNode.serial] = fabricNode.model
    # populate with version info
    fabricNode_ver_list = {}
    firmwareCtrlrRunning_list = md.lookupByClass('firmwareCtrlrRunning')
    for firmwareCtrlrRunning in firmwareCtrlrRunning_list:
        fabricNode_dn = str(firmwareCtrlrRunning.dn).split('/ctrlrfwstatuscont')[0]
        fabricNode_ver_list[fabricNode_dn] = firmwareCtrlrRunning.version
    # Get APIC list
    topSystem_list = md.lookupByClass('topSystem', propFilter='eq(topSystem.role,"controller")')
    data = {}
    data['data'] = []
    for node in topSystem_list:
        entry = []
        entry.append(node.id)
        entry.append(node.name)
        entry.append(node.role)
        entry.append(fabricNode_model_list[node.serial])
        entry.append(node.serial)
        entry.append(fabricNode_ver_list[node.dn])
        entry.append(node.inbMgmtAddr)
        entry.append(node.oobMgmtAddr)
        entry.append(node.state)
        entry.append(node.systemUpTime)
        data['data'].append(entry)
    print_data_table(save_table_data(data))


def show_switch(md):
    # Print the switch list
    print '<h2>Switch List</h2>'
    # print switch info table header
    print '''
    <table id="table_id" class="table table-striped table-bordered" cellspacing="0" width="100%">
        <thead>
            <tr>
                <th>Id</th>
                <th>Name</th>
                <th>Role</th>
                <th>Model</th>
                <th>Serial</th>
                <th>Version</th>
                <th>INB Mgmt IP</th>
                <th>OOB Mgmt IP</th>
                <th>State</th>
                <th>System Uptime</th>
            </tr>
        </thead>
    </table>
    '''
    # populate with model info
    fabricNode_model_list = {}
    fabricNode_list = md.lookupByClass('fabricNode', propFilter='ne(fabricNode.role,"controller")')    
    for fabricNode in fabricNode_list:
        fabricNode_model_list[fabricNode.serial] = fabricNode.model
    # populate with version info
    fabricNode_ver_list = {}
    firmwareRunning_list = md.lookupByClass('firmwareRunning')
    for firmwareRunning in firmwareRunning_list:
        fabricNode_dn = str(firmwareRunning.dn).split('/fwstatuscont')[0]
        fabricNode_ver_list[fabricNode_dn] = firmwareRunning.version
    # Get switch list
    topSystem_list = md.lookupByClass('topSystem', propFilter='ne(topSystem.role,"controller")')
    data = {}
    data['data'] = []
    for node in topSystem_list:
        entry = []
        entry.append(node.id)
        entry.append(node.name)
        entry.append(node.role)
        entry.append(fabricNode_model_list[node.serial])
        entry.append(node.serial)
        entry.append(fabricNode_ver_list[node.dn])
        entry.append(node.inbMgmtAddr)
        entry.append(node.oobMgmtAddr)
        entry.append(node.state)
        entry.append(node.systemUpTime)
        data['data'].append(entry)
    print_data_table(save_table_data(data))


def show_ctrct(apic_url, md, rest):
    # Print the Contract list
    print '<h2>Contract List</h2>'
    # print Contract info table header
    print '''
    <div class="checkbox checkbox-primary">
      <label class="checkbox-inline"><input type="checkbox" id="no_cons">Without Consumer</label>
      <label class="checkbox-inline"><input type="checkbox" id="no_prov">Without Provider</label>
    </div>
    <table id="table_id" class="table table-striped table-bordered" cellspacing="0" width="100%">
        <thead>
            <tr>
                <th>hidden column</th>
                <th>Contract</th>
                <th>Tenant</th>
                <th>Scope</th>
                <th>Subject</th>
                <th>Cons EPG</th>
                <th>Cons L2out</th>
                <th>Cons L3out</th>
                <th>Cons vzAny</th>
                <th>Prov EPG</th>
                <th>Prov L2out</th>
                <th>Prov L3out</th>
                <th>Prov vzAny</th>
            </tr>
        </thead>
    </table>
    '''
    ctrct_list = {}   # construct contract list with parent/child info
    vzBrCP_list = md.lookupByClass('vzBrCP')
    for vzBrCP in vzBrCP_list:
        ctrct_dn = str(vzBrCP.dn)
        ctrct_list[ctrct_dn, 'name'] = vzBrCP.name      # get contract name
        ctrct_list[ctrct_dn, 'tn'] = ctrct_dn.split('/')[1][3:]    # get parent tenant
        ctrct_list[ctrct_dn, 'scope'] = vzBrCP.scope    # get scope
        ctrct_list[ctrct_dn, 'subj'] = ''    # set subject to ''
        ctrct_list[ctrct_dn, 'cons_epg'] = 0    # set consumer epg count to 0
        ctrct_list[ctrct_dn, 'cons_l2out'] = 0    # set consumer l2out count to 0
        ctrct_list[ctrct_dn, 'cons_l3out'] = 0    # set consumer l3out count to 0
        ctrct_list[ctrct_dn, 'cons_vzany'] = 0    # set consumer vzany count to 0
        ctrct_list[ctrct_dn, 'prov_epg'] = 0    # set provider epg count to 0
        ctrct_list[ctrct_dn, 'prov_l2out'] = 0    # set provider l2out count to 0
        ctrct_list[ctrct_dn, 'prov_l3out'] = 0    # set provider l3out count to 0
        ctrct_list[ctrct_dn, 'prov_vzany'] = 0    # set provider vzany count to 0

    # populate with subject info
    vzSubj_list = get_json(rest, '/api/class/vzSubj.json?rsp-prop-include=naming-only')['imdata']
    for vzSubj in vzSubj_list:
        ctrct_dn = str(vzSubj['vzSubj']['attributes']['dn']).split('/subj-')[0]
        if (ctrct_dn, 'subj') in ctrct_list:
            if ctrct_list[ctrct_dn, 'subj'] == '':
                ctrct_list[ctrct_dn, 'subj'] = vzSubj['vzSubj']['attributes']['name']
            else:
                ctrct_list[ctrct_dn, 'subj'] = ctrct_list[ctrct_dn, 'subj'] + '<br>' + vzSubj['vzSubj']['attributes']['name']

    # populate with consumer info
    vzRtCons_list = get_json(rest, '/api/class/vzRtCons.json?rsp-prop-include=naming-only')['imdata']
    for vzRtCons in vzRtCons_list:
        ctrct_dn = str(vzRtCons['vzRtCons']['attributes']['dn']).split('/rtfvCons-')[0]
        if '/out-' in str(vzRtCons['vzRtCons']['attributes']['tDn']):   # l3out
            ctrct_list[ctrct_dn, 'cons_l3out'] += 1
        elif '/l2out-' in str(vzRtCons['vzRtCons']['attributes']['tDn']):   # l2out
            ctrct_list[ctrct_dn, 'cons_l2out'] += 1
        else:   # regular epg
            ctrct_list[ctrct_dn, 'cons_epg'] += 1

    # populate with consumer contract interface info
    ctrct_if_list = {}   # construct list of contract interface which has consumer
    vzRtConsIf_list = get_json(rest, '/api/class/vzRtConsIf.json?rsp-prop-include=naming-only')['imdata']
    for vzRtConsIf in vzRtConsIf_list:
        ctrct_if_dn = str(vzRtConsIf['vzRtConsIf']['attributes']['dn']).split('/rtfvConsIf-')[0]
        if '/out-' in str(vzRtConsIf['vzRtConsIf']['attributes']['tDn']):   # l3out
            if (ctrct_if_dn, 'cons_l3out') in ctrct_if_list:
                ctrct_if_list[ctrct_if_dn, 'cons_l3out'] += 1
            else:
                ctrct_if_list[ctrct_if_dn, 'cons_l3out'] = 1
        elif '/l2out-' in str(vzRtConsIf['vzRtConsIf']['attributes']['tDn']):   # l2out
            if (ctrct_if_dn, 'cons_l2out') in ctrct_if_list:
                ctrct_if_list[ctrct_if_dn, 'cons_l2out'] += 1
            else:
                ctrct_if_list[ctrct_if_dn, 'cons_l2out'] = 1
        else:   # regular epg
            if (ctrct_if_dn, 'cons_epg') in ctrct_if_list:
                ctrct_if_list[ctrct_if_dn, 'cons_epg'] += 1
            else:
                ctrct_if_list[ctrct_if_dn, 'cons_epg'] = 1
    vzRtIf_list = get_json(rest, '/api/class/vzRtIf.json?rsp-prop-include=naming-only')['imdata']
    for vzRtIf in vzRtIf_list:
        ctrct_dn = str(vzRtIf['vzRtIf']['attributes']['dn']).split('/rtif-')[0]
        ctrct_if_dn = str(vzRtIf['vzRtIf']['attributes']['tDn'])
        if (ctrct_if_dn, 'cons_l3out') in ctrct_if_list:    # l3out
            ctrct_list[ctrct_dn, 'cons_l3out'] += ctrct_if_list[ctrct_if_dn, 'cons_l3out']
        if (ctrct_if_dn, 'cons_l2out') in ctrct_if_list:    # l2out
            ctrct_list[ctrct_dn, 'cons_l2out'] += ctrct_if_list[ctrct_if_dn, 'cons_l2out']
        if (ctrct_if_dn, 'cons_epg') in ctrct_if_list:    # regular epg
            ctrct_list[ctrct_dn, 'cons_epg'] += ctrct_if_list[ctrct_if_dn, 'cons_epg']

    # populate with vzAny consumer and consumer interface info
    vzRtAnyToCons_list = md.lookupByClass('vzRtAnyToCons')
    for vzRtAnyToCons in vzRtAnyToCons_list:
        ctrct_dn = str(vzRtAnyToCons.dn).split('/rtanyToCons-')[0]
        ctrct_list[ctrct_dn, 'cons_vzany'] += 1
    vzRtAnyToConsIf_list = md.lookupByClass('vzRtAnyToConsIf')
    for vzRtAnyToConsIf in vzRtAnyToConsIf_list:
        vzCPIf_dn = str(vzRtAnyToConsIf.dn).split('/rtanyToConsIf-')[0]
        vzRsIf = md.lookupByDn('{}/rsif'.format(vzCPIf_dn))
        ctrct_dn = vzRsIf.tDn
        ctrct_list[ctrct_dn, 'cons_vzany'] += 1

    # populate with provider epg info
    vzRtProv_list = get_json(rest, '/api/class/vzRtProv.json?rsp-prop-include=naming-only')['imdata']
    for vzRtProv in vzRtProv_list:
        ctrct_dn = str(vzRtProv['vzRtProv']['attributes']['dn']).split('/rtfvProv-')[0]
        if '/out-' in str(vzRtProv['vzRtProv']['attributes']['tDn']):   # l3out
            ctrct_list[ctrct_dn, 'prov_l3out'] += 1
        elif '/l2out-' in str(vzRtProv['vzRtProv']['attributes']['tDn']):   # l2out
            ctrct_list[ctrct_dn, 'prov_l2out'] += 1
        else:   # regular epg
            ctrct_list[ctrct_dn, 'prov_epg'] += 1

    # populate with vzAny provider info
    vzRtAnyToProv_list = get_json(rest, '/api/class/vzRtAnyToProv.json?rsp-prop-include=naming-only')['imdata']
    for vzRtAnyToProv in vzRtAnyToProv_list:
        ctrct_dn = str(vzRtAnyToProv['vzRtAnyToProv']['attributes']['dn']).split('/rtanyToProv-')[0]
        ctrct_list[ctrct_dn, 'prov_vzany'] += 1

    data = {}
    data['data'] = []
    for vzBrCP in vzBrCP_list:
        entry = []
        ctrct_dn = str(vzBrCP.dn)
        ctrct_url = apic_url + '/#bTenants:' + ctrct_list[ctrct_dn, 'tn'] + '|' + ctrct_dn
        entry.append(ctrct_list[ctrct_dn, 'name'])
        entry.append('<a href="{}" target="_blank">{}</a>'.format(ctrct_url, ctrct_list[ctrct_dn, 'name']))
        entry.append(ctrct_list[ctrct_dn, 'tn'])
        entry.append(ctrct_list[ctrct_dn, 'scope'])
        entry.append('<br>'.join(natsorted(ctrct_list[ctrct_dn, 'subj'].split('<br>'))))
        entry.append(str(ctrct_list[ctrct_dn, 'cons_epg']))
        entry.append(str(ctrct_list[ctrct_dn, 'cons_l2out']))
        entry.append(str(ctrct_list[ctrct_dn, 'cons_l3out']))
        entry.append(str(ctrct_list[ctrct_dn, 'cons_vzany']))
        entry.append(str(ctrct_list[ctrct_dn, 'prov_epg']))
        entry.append(str(ctrct_list[ctrct_dn, 'prov_l2out']))
        entry.append(str(ctrct_list[ctrct_dn, 'prov_l3out']))
        entry.append(str(ctrct_list[ctrct_dn, 'prov_vzany']))
        data['data'].append(entry)
    print_data_table(save_table_data(data), 'hide_first_col')

    # Javascript to show contracts without consumer and/or provider
    temp = Template("""
    <script type="text/javascript">
    $.fn.dataTable.ext.search.push(
        function( settings, data, dataIndex ) {
            var no_cons = $('#no_cons').is(':checked');
            var no_prov = $('#no_prov').is(':checked');
            var cons_epg = parseFloat( data[5] ) || 0; // get data of the consumer epg column
            var cons_l2out = parseFloat( data[6] ) || 0; // get data of the consumer l2out column
            var cons_l3out = parseFloat( data[7] ) || 0; // get data of the consumer l3out column
            var cons_vzany = parseFloat( data[8] ) || 0; // get data of the consumer vzAny column
            var prov_epg = parseFloat( data[9] ) || 0; // get data of the provider epg column
            var prov_l2out = parseFloat( data[10] ) || 0; // get data of the provider l2out column
            var prov_l3out = parseFloat( data[11] ) || 0; // get data of the provider l3out column
            var prov_vzany = parseFloat( data[12] ) || 0; // get data of the provider vzAny column
     
            if ( ( !no_cons && !no_prov ) ||
                 ( no_cons && !no_prov && cons_epg == 0 && cons_l2out == 0 && cons_l3out == 0 && cons_vzany == 0 ) ||
                 ( !no_cons && no_prov && prov_epg == 0 && prov_l2out == 0 && prov_l3out == 0 && prov_vzany == 0 ) ||
                 ( no_cons && no_prov && cons_epg == 0 && cons_l2out == 0 && cons_l3out == 0 && cons_vzany == 0 && prov_epg == 0 && prov_l2out == 0 && prov_l3out == 0 && prov_vzany == 0 ) )
            {
                return true;
            }
            return false;
        }
    );
     
    $(document).ready(function() {
        // Event listener to the range filtering inputs to redraw on input
        $(':checkbox').change( function() {
            table.draw();
        } );
    } );
    </script>
    """)
    print temp.render(locals())


def show_ctrct_detail(apic_url, md, rest):
    # Print the Contract list
    print '<h2>Contract List</h2>'
    # print Contract info table header
    print '''
    <table id="table_id" class="table table-striped table-bordered" cellspacing="0" width="100%">
        <thead>
            <tr>
                <th>hidden column</th>
                <th>Contract</th>
                <th>Tenant</th>
                <th>Scope</th>
                <th>Subject</th>
                <th>Cons EPG</th>
                <th>Cons L2out</th>
                <th>Cons L3out</th>
                <th>Cons vzAny</th>
                <th>Prov EPG</th>
                <th>Prov L2out</th>
                <th>Prov L3out</th>
                <th>Prov vzAny</th>
            </tr>
        </thead>
    </table>
    '''
    ctrct_list = {}   # construct contract list with parent/child info
    vzBrCP_list = md.lookupByClass('vzBrCP')
    for vzBrCP in vzBrCP_list:
        ctrct_dn = str(vzBrCP.dn)
        ctrct_list[ctrct_dn, 'name'] = vzBrCP.name      # get contract name
        ctrct_list[ctrct_dn, 'tn'] = ctrct_dn.split('/')[1][3:]    # get parent tenant
        ctrct_list[ctrct_dn, 'scope'] = vzBrCP.scope    # get scope
        ctrct_list[ctrct_dn, 'subj'] = ''    # set subject to ''
        ctrct_list[ctrct_dn, 'cons_epg'] = ''    # set consumer epg to ''
        ctrct_list[ctrct_dn, 'cons_l2out'] = ''    # set consumer l2out to ''
        ctrct_list[ctrct_dn, 'cons_l3out'] = ''    # set consumer l3out to ''
        ctrct_list[ctrct_dn, 'cons_vzany'] = ''    # set consumer vzany to ''
        ctrct_list[ctrct_dn, 'prov_epg'] = ''    # set provider epg to ''
        ctrct_list[ctrct_dn, 'prov_l2out'] = ''    # set provider l2out to ''
        ctrct_list[ctrct_dn, 'prov_l3out'] = ''    # set provider l3out to ''
        ctrct_list[ctrct_dn, 'prov_vzany'] = ''    # set provider vzany to ''

    # populate with subject info
    vzSubj_list = get_json(rest, '/api/class/vzSubj.json?rsp-prop-include=naming-only')['imdata']
    for vzSubj in vzSubj_list:
        ctrct_dn = str(vzSubj['vzSubj']['attributes']['dn']).split('/subj-')[0]
        if (ctrct_dn, 'subj') in ctrct_list:
            if ctrct_list[ctrct_dn, 'subj'] == '':
                ctrct_list[ctrct_dn, 'subj'] = vzSubj['vzSubj']['attributes']['name']
            else:
                ctrct_list[ctrct_dn, 'subj'] = ctrct_list[ctrct_dn, 'subj'] + '<br>' + vzSubj['vzSubj']['attributes']['name']

    # populate with consumer info
    vzRtCons_list = get_json(rest, '/api/class/vzRtCons.json?rsp-prop-include=naming-only')['imdata']
    for vzRtCons in vzRtCons_list:
        ctrct_dn = str(vzRtCons['vzRtCons']['attributes']['dn']).split('/rtfvCons-')[0]
        tDn = str(vzRtCons['vzRtCons']['attributes']['tDn'])
        if '/out-' in tDn:   # l3out
            uni, tn, out, instP = tDn.split('/')
            l3out_name = '/'.join([tn[3:], out[4:], instP[6:]])
            if ctrct_list[ctrct_dn, 'cons_l3out'] == '':
                ctrct_list[ctrct_dn, 'cons_l3out'] = l3out_name
            else:
                ctrct_list[ctrct_dn, 'cons_l3out'] = ctrct_list[ctrct_dn, 'cons_l3out'] + '<br>' + l3out_name
        elif '/l2out-' in tDn:   # l2out
            uni, tn, l2out, instP = tDn.split('/')
            l2out_name = '/'.join([tn[3:], l2out[6:], instP[6:]])
            if ctrct_list[ctrct_dn, 'cons_l2out'] == '':
                ctrct_list[ctrct_dn, 'cons_l2out'] = l2out_name
            else:
                ctrct_list[ctrct_dn, 'cons_l2out'] = ctrct_list[ctrct_dn, 'cons_l2out'] + '<br>' + l2out_name
        else:   # regular epg
            uni, tn, ap, epg = tDn.split('/')
            epg_name = '/'.join([tn[3:], ap[3:], epg[4:]])
            if ctrct_list[ctrct_dn, 'cons_epg'] == '':
                ctrct_list[ctrct_dn, 'cons_epg'] = epg_name
            else:
                ctrct_list[ctrct_dn, 'cons_epg'] = ctrct_list[ctrct_dn, 'cons_epg'] + '<br>' + epg_name

    # populate with consumer contract interface info
    ctrct_if_list = {}   # construct list of contract interface which has consumer
    vzRtConsIf_list = get_json(rest, '/api/class/vzRtConsIf.json?rsp-prop-include=naming-only')['imdata']
    for vzRtConsIf in vzRtConsIf_list:
        ctrct_if_dn = str(vzRtConsIf['vzRtConsIf']['attributes']['dn']).split('/rtfvConsIf-')[0]
        tDn = str(vzRtConsIf['vzRtConsIf']['attributes']['tDn'])
        if '/out-' in tDn:   # l3out
            uni, tn, out, instP = tDn.split('/')
            l3out_name = '/'.join([tn[3:], out[4:], instP[6:]])
            if (ctrct_if_dn, 'cons_l3out') in ctrct_if_list:
                ctrct_if_list[ctrct_if_dn, 'cons_l3out'] = ctrct_if_list[ctrct_if_dn, 'cons_l3out'] + '<br><i>' + l3out_name + '</i>'
            else:
                ctrct_if_list[ctrct_if_dn, 'cons_l3out'] = '<i>' + l3out_name + '</i>'
        elif '/l2out-' in tDn:   # l2out
            uni, tn, l2out, instP = tDn.split('/')
            l2out_name = '/'.join([tn[3:], l2out[6:], instP[6:]])
            if (ctrct_if_dn, 'cons_l2out') in ctrct_if_list:
                ctrct_if_list[ctrct_if_dn, 'cons_l2out'] = ctrct_if_list[ctrct_if_dn, 'cons_l2out'] + '<br><i>' + l2out_name + '</i>'
            else:
                ctrct_if_list[ctrct_if_dn, 'cons_l2out'] = '<i>' + l2out_name + '</i>'
        else:   # regular epg
            uni, tn, ap, epg = tDn.split('/')
            epg_name = '/'.join([tn[3:], ap[3:], epg[4:]])
            if (ctrct_if_dn, 'cons_epg') in ctrct_if_list:
                ctrct_if_list[ctrct_if_dn, 'cons_epg'] = ctrct_if_list[ctrct_if_dn, 'cons_epg'] + '<br><i>' + epg_name + '</i>'
            else:
                ctrct_if_list[ctrct_if_dn, 'cons_epg'] = '<i>' + epg_name + '</i>'
    vzRtIf_list = get_json(rest, '/api/class/vzRtIf.json?rsp-prop-include=naming-only')['imdata']
    for vzRtIf in vzRtIf_list:
        ctrct_dn = str(vzRtIf['vzRtIf']['attributes']['dn']).split('/rtif-')[0]
        ctrct_if_dn = str(vzRtIf['vzRtIf']['attributes']['tDn'])
        if (ctrct_if_dn, 'cons_l3out') in ctrct_if_list:    # l3out
            if ctrct_list[ctrct_dn, 'cons_l3out'] == '':
                ctrct_list[ctrct_dn, 'cons_l3out'] = ctrct_if_list[ctrct_if_dn, 'cons_l3out']
            else:
                ctrct_list[ctrct_dn, 'cons_l3out'] = ctrct_list[ctrct_dn, 'cons_l3out'] + '<br>' + ctrct_if_list[ctrct_if_dn, 'cons_l3out']
        if (ctrct_if_dn, 'cons_l2out') in ctrct_if_list:    # l2out
            if ctrct_list[ctrct_dn, 'cons_l2out'] == '':
                ctrct_list[ctrct_dn, 'cons_l2out'] = ctrct_if_list[ctrct_if_dn, 'cons_l2out']
            else:
                ctrct_list[ctrct_dn, 'cons_l2out'] = ctrct_list[ctrct_dn, 'cons_l2out'] + '<br>' + ctrct_if_list[ctrct_if_dn, 'cons_l2out']
        if (ctrct_if_dn, 'cons_epg') in ctrct_if_list:    # regular epg
            if ctrct_list[ctrct_dn, 'cons_epg'] == '':
                ctrct_list[ctrct_dn, 'cons_epg'] = ctrct_if_list[ctrct_if_dn, 'cons_epg']
            else:
                ctrct_list[ctrct_dn, 'cons_epg'] = ctrct_list[ctrct_dn, 'cons_epg'] + '<br>' + ctrct_if_list[ctrct_if_dn, 'cons_epg']

    # populate with vzAny consumer and consumer interface info
    vzRtAnyToCons_list = md.lookupByClass('vzRtAnyToCons')
    for vzRtAnyToCons in vzRtAnyToCons_list:
        ctrct_dn = str(vzRtAnyToCons.dn).split('/rtanyToCons-')[0]
        tDn = vzRtAnyToCons.tDn
        uni, tn, ctx, any = tDn.split('/')
        vzany_name = '/'.join([tn[3:], ctx[4:], any])
        if ctrct_list[ctrct_dn, 'cons_vzany'] == '':
            ctrct_list[ctrct_dn, 'cons_vzany'] = vzany_name
        else:
            ctrct_list[ctrct_dn, 'cons_vzany'] = ctrct_list[ctrct_dn, 'cons_vzany'] + '<br>' + vzany_name
    vzRtAnyToConsIf_list = md.lookupByClass('vzRtAnyToConsIf')
    for vzRtAnyToConsIf in vzRtAnyToConsIf_list:
        vzCPIf_dn = str(vzRtAnyToConsIf.dn).split('/rtanyToConsIf-')[0]
        vzRsIf = md.lookupByDn('{}/rsif'.format(vzCPIf_dn))
        ctrct_dn = vzRsIf.tDn
        tDn = vzRtAnyToConsIf.tDn
        uni, tn, ctx, any = tDn.split('/')
        vzany_name = '/'.join([tn[3:], ctx[4:], any])
        if ctrct_list[ctrct_dn, 'cons_vzany'] == '':
            ctrct_list[ctrct_dn, 'cons_vzany'] = '<i>' + vzany_name + '</i>'
        else:
            ctrct_list[ctrct_dn, 'cons_vzany'] = ctrct_list[ctrct_dn, 'cons_vzany'] + '<br><i>' + vzany_name + '</i>'

    # populate with provider epg info
    vzRtProv_list = get_json(rest, '/api/class/vzRtProv.json?rsp-prop-include=naming-only')['imdata']
    for vzRtProv in vzRtProv_list:
        ctrct_dn = str(vzRtProv['vzRtProv']['attributes']['dn']).split('/rtfvProv-')[0]
        tDn = str(vzRtProv['vzRtProv']['attributes']['tDn'])
        if '/out-' in tDn:   # l3out
            uni, tn, out, instP = tDn.split('/')
            l3out_name = '/'.join([tn[3:], out[4:], instP[6:]])
            if ctrct_list[ctrct_dn, 'prov_l3out'] == '':
                ctrct_list[ctrct_dn, 'prov_l3out'] = l3out_name
            else:
                ctrct_list[ctrct_dn, 'prov_l3out'] = ctrct_list[ctrct_dn, 'prov_l3out'] + '<br>' + l3out_name
        elif '/l2out-' in tDn:   # l2out
            uni, tn, l2out, instP = tDn.split('/')
            l2out_name = '/'.join([tn[3:], l2out[6:], instP[6:]])
            if ctrct_list[ctrct_dn, 'prov_l2out'] == '':
                ctrct_list[ctrct_dn, 'prov_l2out'] = l2out_name
            else:
                ctrct_list[ctrct_dn, 'prov_l2out'] = ctrct_list[ctrct_dn, 'prov_l2out'] + '<br>' + l2out_name
        else:   # regular epg
            uni, tn, ap, epg = tDn.split('/')
            epg_name = '/'.join([tn[3:], ap[3:], epg[4:]])
            if ctrct_list[ctrct_dn, 'prov_epg'] == '':
                ctrct_list[ctrct_dn, 'prov_epg'] = epg_name
            else:
                ctrct_list[ctrct_dn, 'prov_epg'] = ctrct_list[ctrct_dn, 'prov_epg'] + '<br>' + epg_name

    # populate with vzAny provider info
    vzRtAnyToProv_list = get_json(rest, '/api/class/vzRtAnyToProv.json?rsp-prop-include=naming-only')['imdata']
    for vzRtAnyToProv in vzRtAnyToProv_list:
        ctrct_dn = str(vzRtAnyToProv['vzRtAnyToProv']['attributes']['dn']).split('/rtanyToProv-')[0]
        tDn = str(vzRtAnyToProv['vzRtAnyToProv']['attributes']['tDn'])
        uni, tn, ctx, any = tDn.split('/')
        vzany_name = '/'.join([tn[3:], ctx[4:], any])
        if ctrct_list[ctrct_dn, 'prov_vzany'] == '':
            ctrct_list[ctrct_dn, 'prov_vzany'] = vzany_name
        else:
            ctrct_list[ctrct_dn, 'prov_vzany'] = ctrct_list[ctrct_dn, 'prov_vzany'] + '<br>' + vzany_name

    data = {}
    data['data'] = []
    for vzBrCP in vzBrCP_list:
        entry = []
        ctrct_dn = str(vzBrCP.dn)
        ctrct_url = apic_url + '/#bTenants:' + ctrct_list[ctrct_dn, 'tn'] + '|' + ctrct_dn
        entry.append(ctrct_list[ctrct_dn, 'name'])
        entry.append('<a href="{}" target="_blank">{}</a>'.format(ctrct_url, ctrct_list[ctrct_dn, 'name']))
        entry.append(ctrct_list[ctrct_dn, 'tn'])
        entry.append(ctrct_list[ctrct_dn, 'scope'])
        entry.append('<br>'.join(natsorted(ctrct_list[ctrct_dn, 'subj'].split('<br>'))))
        entry.append('<br>'.join(natsorted(ctrct_list[ctrct_dn, 'cons_epg'].split('<br>'))))
        entry.append('<br>'.join(natsorted(ctrct_list[ctrct_dn, 'cons_l2out'].split('<br>'))))
        entry.append('<br>'.join(natsorted(ctrct_list[ctrct_dn, 'cons_l3out'].split('<br>'))))
        entry.append('<br>'.join(natsorted(ctrct_list[ctrct_dn, 'cons_vzany'].split('<br>'))))
        entry.append('<br>'.join(natsorted(ctrct_list[ctrct_dn, 'prov_epg'].split('<br>'))))
        entry.append('<br>'.join(natsorted(ctrct_list[ctrct_dn, 'prov_l2out'].split('<br>'))))
        entry.append('<br>'.join(natsorted(ctrct_list[ctrct_dn, 'prov_l3out'].split('<br>'))))
        entry.append('<br>'.join(natsorted(ctrct_list[ctrct_dn, 'prov_vzany'].split('<br>'))))
        data['data'].append(entry)
    print_data_table(save_table_data(data), 'hide_first_col')


def show_ep(rest):
    # Print the endpoint list
    print '<h2>Endpoint List</h2>'
    # print endpoint info table header
    print '''
    <table id="table_id" class="table table-striped table-bordered" cellspacing="0" width="100%">
        <thead>
            <tr>
                <th><i>EPG</i> / Port Group</th>
                <th>End Point</th>
                <th>MAC Address</th>
                <th>IP Address</th>
                <th>Learning Source</th>
                <th>Controller</th>
                <th>Interface</th>
                <th>Encap</th>
            </tr>
        </thead>
    </table>
    '''
    # get fvCEp list
    pc, ps = get_page_info(rest, 'fvCEp')
    if pc > 1:
        fvCEp_list = get_json_parallel(rest, pc, ps, '/api/class/fvCEp.json?order-by=fvCEp.mac')
    else:
        fvCEp_list = get_json(rest, '/api/class/fvCEp.json')['imdata']

    # populate with VM endpoint name and controller info
    fvCEp_vm_ctrlr_list = {}
    fvCEp_vm_name_list = {}
    compVm_list = {}
    compHv_list = {}
    for compVm in get_json(rest, '/api/class/compVm.json')['imdata']:
        compVm_list[compVm['compVm']['attributes']['dn']] = compVm['compVm']['attributes']['name']
    for compHv in get_json(rest, '/api/class/compHv.json')['imdata']:
        compHv_list[compHv['compHv']['attributes']['dn']] = compHv['compHv']['attributes']['name']
    for fvRsVm in get_json(rest, '/api/class/fvRsVm.json')['imdata']:
        fvCEp_dn = str(fvRsVm['fvRsVm']['attributes']['dn']).split('/rsvm')[0]
        fvCEp_vm_ctrlr_list[fvCEp_dn] = fvRsVm['fvRsVm']['attributes']['tDn'].split('/')[2].split(']-')[1]
        if fvRsVm['fvRsVm']['attributes']['tDn'] in compVm_list:
            fvCEp_vm_name_list[fvCEp_dn] = compVm_list[fvRsVm['fvRsVm']['attributes']['tDn']]
        elif fvRsVm['fvRsVm']['attributes']['tDn'] in compHv_list:
            fvCEp_vm_name_list[fvCEp_dn] = compHv_list[fvRsVm['fvRsVm']['attributes']['tDn']]

    # populate with endpoint IP info
    fvCEp_ip_list = {}
    if pc > 1:
        fvIp_list = get_json_parallel(rest, pc, ps, '/api/class/fvIp.json?rsp-prop-include=naming-only&order-by=fvIp.addr')
    else:
        fvIp_list = get_json(rest, '/api/class/fvIp.json?rsp-prop-include=naming-only')['imdata']
    for fvIp in fvIp_list:
        fvCEp_dn = str(fvIp['fvIp']['attributes']['dn']).split('/ip-')[0]
        if fvCEp_dn in fvCEp_ip_list:
            fvCEp_ip_list[fvCEp_dn] = fvCEp_ip_list[fvCEp_dn] + '<br>' + fvIp['fvIp']['attributes']['addr']
        else:
            fvCEp_ip_list[fvCEp_dn] = fvIp['fvIp']['attributes']['addr']

    # populate with endpoint interface info
    fvCEp_if_list = {}
    if pc > 1:
        fvRsCEpToPathEp_list = get_json_parallel(rest, pc, ps, '/api/class/fvRsCEpToPathEp.json?order-by=fvRsCEpToPathEp.modTs')
    else:
        fvRsCEpToPathEp_list = get_json(rest, '/api/class/fvRsCEpToPathEp.json?rsp-prop-include=naming-only')['imdata']
    for fvRsCEpToPathEp in fvRsCEpToPathEp_list:
        fvCEp_dn = str(fvRsCEpToPathEp['fvRsCEpToPathEp']['attributes']['dn']).split('/rscEpToPathEp-')[0]
        if '/pathgrp-' in fvRsCEpToPathEp['fvRsCEpToPathEp']['attributes']['tDn']:
            intf = fvRsCEpToPathEp['fvRsCEpToPathEp']['attributes']['tDn'].split('/pathgrp-')[1][1:-1]
        else:
            match = re.match('topology/pod-(.*)/(prot)?paths-(.*)/pathep-\[(.*)]', str(fvRsCEpToPathEp['fvRsCEpToPathEp']['attributes']['tDn']))
            #intf = match.group(1) + '/' + match.group(3) + '/' + match.group(4) # get interface name
            intf = match.group(3) + '/' + match.group(4) # get interface name
        if fvCEp_dn in fvCEp_if_list:
            fvCEp_if_list[fvCEp_dn] = fvCEp_if_list[fvCEp_dn] + '<br>' + intf
        else:
            fvCEp_if_list[fvCEp_dn] = intf

    compEpPConn_list = {}
    for compEpPConn in get_json(rest, '/api/class/compEpPConn.json')['imdata']:
        if '/vnic-' in str(compEpPConn['compEpPConn']['attributes']['dn']):
            fvCEp_mac = str(compEpPConn['compEpPConn']['attributes']['dn']).split('/vnic-')[1][:17]
            compEpPConn_list[fvCEp_mac] = compEpPConn['compEpPConn']['attributes']['epgPKey']
    data = {}
    data['data'] = []
    for fvCEp in fvCEp_list:
        entry = []
        fvCEp_dn = str(fvCEp['fvCEp']['attributes']['dn'])
        port_group = fvCEp_dn.split('/cep-')[0]
        if '/ldev-' in port_group or '/LDevInst-' in port_group:   # For ldev, find PG from vmnic
            try:
                port_group = compEpPConn_list[fvCEp_dn.split('/cep-')[1]]
                tn = port_group.split('/')[1][3:]    # get tenant name
                ap = port_group.split('/')[2][3:]    # get application profile name
                epg = port_group.split('/')[3][4:]    # get epg name
                port_group = '|'.join([tn, ap, epg])
            except:
                port_group = port_group.split('/LDevInst-')[0].split('/tn-')[1] + '/' + port_group.split('/LDevInst-')[1].replace('/G-', '/')
        else:
            tn = port_group.split('/')[1][3:]    # get tenant name
            ap = port_group.split('/')[2][3:]    # get application profile name
            epg = port_group.split('/')[3][4:]    # get epg name
            port_group = '|'.join([tn, ap, epg])
        if '[uni/' in port_group:
            entry.append('<i>{}</i>'.format(port_group))
        else:
            entry.append(port_group)
        if 'vmm' in fvCEp['fvCEp']['attributes']['lcC']:
            if fvCEp_dn in fvCEp_vm_name_list:
                entry.append(fvCEp_vm_name_list[fvCEp_dn])
            elif fvCEp['fvCEp']['attributes']['vmmSrc'] == 'ovs':
                entry.append(fvCEp['fvCEp']['attributes']['contName'])
            elif fvCEp['fvCEp']['attributes']['name'] != '':
                entry.append('EP-{}'.format(fvCEp['fvCEp']['attributes']['name']))
            else:
                entry.append('&nbsp;')
        else:
            entry.append('EP-{}'.format(fvCEp['fvCEp']['attributes']['mac']))
        entry.append(fvCEp['fvCEp']['attributes']['mac'])
        if fvCEp_dn in fvCEp_ip_list:
            entry.append('<br>'.join(natsorted(fvCEp_ip_list[fvCEp_dn].split('<br>'))))
        else:
            entry.append('&nbsp;')
        entry.append(fvCEp['fvCEp']['attributes']['lcC'].replace(',', '<br>'))
        vmm_ctrlr = '&nbsp;'
        if 'vmm' in fvCEp['fvCEp']['attributes']['lcC']:
            if fvCEp_dn in fvCEp_vm_ctrlr_list:
                vmm_ctrlr = fvCEp_vm_ctrlr_list[fvCEp_dn]
            elif fvCEp['fvCEp']['attributes']['vmmSrc'] == 'ovs':     # check ovs controller name
                vmmEpPD = get_json(rest, '/api/class/vmmEpPD.json?rsp-prop-include=naming-only&query-target-filter=wcard(vmmEpPD.epgPKey,"{}")'.format(fvCEp_dn.split('/cep-')[0]))['imdata']
                vmm_ctrlr = str(vmmEpPD[0]['vmmEpPD']['attributes']['dn']).split('/')[2][4:]
        entry.append(vmm_ctrlr)
        if fvCEp_dn in fvCEp_if_list:
            entry.append('<br>'.join(natsorted(fvCEp_if_list[fvCEp_dn].split('<br>'))))
        else:
            entry.append('&nbsp;')
        entry.append(fvCEp['fvCEp']['attributes']['encap'])
        data['data'].append(entry)
    print_data_table(save_table_data(data))


def show_epg(apic_url, rest):
    # Print the EPG list
    print '<h2>EPG List</h2>'
    # print EPG info table header
    print '''
    <table id="table_id" class="table table-striped table-bordered" cellspacing="0" width="100%">
        <thead>
            <tr>
                <th>hidden column</th>
                <th>EPG</th>
                <th>Tenant</th>
                <th>Context</th>
                <th>Bridge Domain</th>
                <th>App Profile</th>
                <th>Consumed Contract / <i>Interface</i></th>
                <th>Provided Contract</th>
                <th>Static Bindings (Path)</th>
                <th>Encap</th>
                <th>Subnets</th>
                <th>Domains</th>
            </tr>
        </thead>
    </table>
    '''
    ctx_list = {}   # construct context list
    for fvCtx in get_json(rest, '/api/class/fvCtx.json')['imdata']:
        ctx_list[fvCtx['fvCtx']['attributes']['scope']] = fvCtx['fvCtx']['attributes']['name']

    epg_list = {}   # construct epg list with parent/child info
    fvAEPg_list = get_json(rest, '/api/class/fvAEPg.json')['imdata']
    for fvAEPg in fvAEPg_list:
        epg_dn = str(fvAEPg['fvAEPg']['attributes']['dn'])
        epg_list[epg_dn, 'name'] = fvAEPg['fvAEPg']['attributes']['name']
        epg_list[epg_dn, 'tn'] = epg_dn.split('/')[1][3:]    # get parent tenant
        epg_list[epg_dn, 'ap'] = epg_dn.split('/')[2][3:]    # get parent ap
        epg_list[epg_dn, 'bd'] = ''    # set bd to ''
        epg_list[epg_dn, 'cons_ctrct'] = ''    # set consumed contract to ''
        epg_list[epg_dn, 'prov_ctrct'] = ''    # set provided contract to ''
        epg_list[epg_dn, 'rspathAtt'] = ''    # set rspathAtt to ''
        epg_list[epg_dn, 'encap'] = ''    # set encap to ''
        epg_list[epg_dn, 'subnet'] = ''    # set subnet to ''
        epg_list[epg_dn, 'domain'] = ''    # set domain to ''

    # populate with Bridge Domain info
    for fvRsBd in get_json(rest, '/api/class/fvRsBd.json')['imdata']:
        epg_dn = str(fvRsBd['fvRsBd']['attributes']['dn']).split('/rsbd')[0]
        epg_list[epg_dn, 'bd'] = fvRsBd['fvRsBd']['attributes']['tnFvBDName']

    # populate with consumed contract info
    fvRsCons_list = get_json(rest, '/api/class/fvRsCons.json?rsp-prop-include=naming-only&query-target-filter=not(wcard(fvRsCons.dn,"/out-"))')['imdata']
    for fvRsCons in fvRsCons_list:
        # regular epg, e.g. uni/tn-scale39/ap-prod/epg-prd.app/rscons-common-omn_splunk
        fvRsCons_dn = str(fvRsCons['fvRsCons']['attributes']['dn'])
        if '/out-' not in fvRsCons_dn and '/mgmtp-' not in fvRsCons_dn and '/l2out-' not in fvRsCons_dn:
            epg_dn = fvRsCons_dn.split('/rscons-')[0]
            if epg_list[epg_dn, 'cons_ctrct'] == '':
                epg_list[epg_dn, 'cons_ctrct'] = fvRsCons['fvRsCons']['attributes']['tnVzBrCPName']
            else:
                epg_list[epg_dn, 'cons_ctrct'] = epg_list[epg_dn, 'cons_ctrct'] + '<br>' + fvRsCons['fvRsCons']['attributes']['tnVzBrCPName']

    # populate with consumed contract interface info
    fvRsConsIf_list = get_json(rest, '/api/class/fvRsConsIf.json?rsp-prop-include=naming-only&query-target-filter=not(wcard(fvRsConsIf.dn,"/out-"))')['imdata']
    for fvRsConsIf in fvRsConsIf_list:
        epg_dn = str(fvRsConsIf['fvRsConsIf']['attributes']['dn']).split('/rsconsIf-')[0]
        if epg_list[epg_dn, 'cons_ctrct'] == '':
            epg_list[epg_dn, 'cons_ctrct'] = '<i>' + fvRsConsIf['fvRsConsIf']['attributes']['tnVzCPIfName'] + '</i>'
        else:
            epg_list[epg_dn, 'cons_ctrct'] = epg_list[epg_dn, 'cons_ctrct'] + '<br><i>' + fvRsConsIf['fvRsConsIf']['attributes']['tnVzCPIfName'] + '</i>'

    # populate with provided contract info
    fvRsProv_list = get_json(rest, '/api/class/fvRsProv.json?rsp-prop-include=naming-only')['imdata']
    for fvRsProv in fvRsProv_list:
        #uni/tn-mgmt/mgmtp-default/inb-spineInbandEPG/rsprov-default 
        #uni/tn-tn-iptv/l2out-l2Out1/instP-l2inst1
        fvRsProv_dn = str(fvRsProv['fvRsProv']['attributes']['dn'])
        if '/out-' not in fvRsProv_dn and '/mgmtp-' not in fvRsProv_dn and '/l2out-' not in fvRsProv_dn:
            epg_dn = fvRsProv_dn.split('/rsprov-')[0]
            if epg_list[epg_dn, 'prov_ctrct'] == '':
                epg_list[epg_dn, 'prov_ctrct'] = fvRsProv['fvRsProv']['attributes']['tnVzBrCPName']
            else:
                epg_list[epg_dn, 'prov_ctrct'] = epg_list[epg_dn, 'prov_ctrct'] + '<br>' + fvRsProv['fvRsProv']['attributes']['tnVzBrCPName']

    # populate with static binding (path) info
    json_data = get_json(rest, '/api/class/fvRsPathAtt.json?rsp-prop-include=config-only')
    if json_data is False:    # use incremental lookup if the dataset is too big
        fvRsPathAtt_list = get_json(rest, '/api/class/fvRsPathAtt.json?rsp-prop-include=config-only&query-target-filter=not(wcard(fvRsPathAtt.encap,"vlan-"))')['imdata']
        for num in range(1, 10):
            fvRsPathAtt_list += get_json(rest, '/api/class/fvRsPathAtt.json?rsp-prop-include=config-only&query-target-filter=wcard(fvRsPathAtt.encap,"vlan-{}")'.format(num))['imdata']
    else:
        fvRsPathAtt_list = json_data['imdata']
    for fvRsPathAtt in fvRsPathAtt_list:
        epg_dn = str(fvRsPathAtt['fvRsPathAtt']['attributes']['dn']).split('/rspathAtt-')[0]
        match = re.match('topology/pod-(.*)/(prot)?paths-(.*)/pathep-\[(.*)]', str(fvRsPathAtt['fvRsPathAtt']['attributes']['tDn']))
        #intf = match.group(1) + '/' + match.group(3) + '/' + match.group(4) # get interface name
        intf = match.group(3) + '/' + match.group(4) # get interface name
        if epg_list[epg_dn, 'rspathAtt'] == '':
            epg_list[epg_dn, 'rspathAtt'] = intf
            epg_list[epg_dn, 'encap'] = fvRsPathAtt['fvRsPathAtt']['attributes']['encap']
        else:
            epg_list[epg_dn, 'rspathAtt'] = epg_list[epg_dn, 'rspathAtt'] + '<br>' + intf
            epg_list[epg_dn, 'encap'] = epg_list[epg_dn, 'encap'] + '<br>' + fvRsPathAtt['fvRsPathAtt']['attributes']['encap']

    # populate with subnets info
    fvSubnet_list = get_json(rest, '/api/class/fvAEPg.json?query-target=subtree&target-subtree-class=fvSubnet')['imdata']
    for fvSubnet in fvSubnet_list:
        epg_dn = str(fvSubnet['fvSubnet']['attributes']['dn']).split('/subnet-')[0]
        if epg_list[epg_dn, 'subnet'] == '':
            epg_list[epg_dn, 'subnet'] = fvSubnet['fvSubnet']['attributes']['ip']
        else:
            epg_list[epg_dn, 'subnet'] = epg_list[epg_dn, 'subnet'] + '<br>' +  fvSubnet['fvSubnet']['attributes']['ip']

    # populate with domains info
    for fvRsDomAtt in get_json(rest, '/api/class/fvRsDomAtt.json?rsp-prop-include=naming-only&query-target-filter=eq(fvRsDomAtt.tCl,"physDomP")')['imdata']:
        epg_dn = str(fvRsDomAtt['fvRsDomAtt']['attributes']['dn']).split('/rsdomAtt-')[0]
        domain = fvRsDomAtt['fvRsDomAtt']['attributes']['tDn'].split('/phys-')[1]
        if epg_list[epg_dn, 'domain'] == '':
            epg_list[epg_dn, 'domain'] = domain
        else:
            epg_list[epg_dn, 'domain'] = epg_list[epg_dn, 'domain'] + '<br>' + domain
    for fvRsDomAtt in get_json(rest, '/api/class/fvRsDomAtt.json?rsp-prop-include=naming-only&query-target-filter=eq(fvRsDomAtt.tCl,"vmmDomP")')['imdata']:
        epg_dn = str(fvRsDomAtt['fvRsDomAtt']['attributes']['dn']).split('/rsdomAtt-')[0]
        domain = fvRsDomAtt['fvRsDomAtt']['attributes']['tDn'].split('/dom-')[1]
        if epg_list[epg_dn, 'domain'] == '':
            epg_list[epg_dn, 'domain'] = domain
        else:
            epg_list[epg_dn, 'domain'] = epg_list[epg_dn, 'domain'] + '<br>' + domain

    data = {}
    data['data'] = []
    for fvAEPg in fvAEPg_list:
        entry = []
        epg_dn = str(fvAEPg['fvAEPg']['attributes']['dn'])
        epg_url = apic_url + '/#bTenants:' + epg_list[epg_dn, 'tn'] + '|' + epg_dn
        entry.append(fvAEPg['fvAEPg']['attributes']['name'])
        entry.append('<a href="{}" target="_blank">{}</a>'.format(epg_url, fvAEPg['fvAEPg']['attributes']['name']))
        entry.append(epg_list[epg_dn, 'tn'])
        if fvAEPg['fvAEPg']['attributes']['scope'] in ctx_list:
            entry.append(ctx_list[fvAEPg['fvAEPg']['attributes']['scope']])
        else:
            entry.append('&nbsp;')
        entry.append(epg_list[epg_dn, 'bd'])
        entry.append(epg_list[epg_dn, 'ap'])
        entry.append('<br>'.join(natsorted(epg_list[epg_dn, 'cons_ctrct'].split('<br>'))))
        entry.append('<br>'.join(natsorted(epg_list[epg_dn, 'prov_ctrct'].split('<br>'))))
        entry.append('<br>'.join(natsorted(epg_list[epg_dn, 'rspathAtt'].split('<br>'))))
        entry.append('<br>'.join(natsorted(set(epg_list[epg_dn, 'encap'].split('<br>')))))
        entry.append('<br>'.join(natsorted(set(epg_list[epg_dn, 'subnet'].split('<br>')))))
        entry.append('<br>'.join(natsorted(set(epg_list[epg_dn, 'domain'].split('<br>')))))
        data['data'].append(entry)
    print_data_table(save_table_data(data), 'hide_first_col')


def show_instP(apic_url, md, rest):
    # Print the L3 External Network Instance Profile, a.k.a, L3out EPG list
    print '<h2>L3 External Network Instance Profile List</h2>'
    # print L3out EPG info table header
    print '''
    <table id="table_id" class="table table-striped table-bordered" cellspacing="0" width="100%">
        <thead>
            <tr>
                <th>hidden column</th>
                <th>L3 External Network</th>
                <th>Tenant</th>
                <th>Context</th>
                <th>L3 Outside</th>
                <th>Subnets</th>
                <th>Consumed Contract / <i>Interface</i></th>
                <th>Provided Contract</th>
            </tr>
        </thead>
    </table>
    '''
    ctx_list = {}   # construct context list
    ctxs = md.lookupByClass('fvCtx')
    for ctx in ctxs:
        ctx_list[ctx.scope] = ctx.name

    instP_list = {}   # construct l3out instP list with parent/child info
    l3extInstP_list = md.lookupByClass('l3extInstP')
    for l3extInstP in l3extInstP_list:
        instP_dn = str(l3extInstP.dn)
        instP_list[instP_dn, 'name'] = l3extInstP.name
        instP_list[instP_dn, 'tn'] = instP_dn.split('/')[1][3:]    # get parent tenant
        instP_list[instP_dn, 'l3out'] = instP_dn.split('/')[2][4:]    # get parent L3out
        instP_list[instP_dn, 'subnet'] = ''    # set subnet to ''
        instP_list[instP_dn, 'cons_ctrct'] = ''    # set consumed contract to ''
        instP_list[instP_dn, 'prov_ctrct'] = ''    # set provided contract to ''

    # populate with subnet info
    for l3extSubnet in get_json(rest, '/api/class/l3extSubnet.json')['imdata']:
        instP_dn = str(l3extSubnet['l3extSubnet']['attributes']['dn']).split('/extsubnet-')[0]
        if 'import' in l3extSubnet['l3extSubnet']['attributes']['scope'] and 'export' in l3extSubnet['l3extSubnet']['attributes']['scope']:
            icon = '<span class="glyphicon glyphicon-transfer"></span>&nbsp;'
        elif 'import' in l3extSubnet['l3extSubnet']['attributes']['scope']:
            icon = '<span class="glyphicon glyphicon-resize-small"></span>&nbsp;'
        elif 'export' in l3extSubnet['l3extSubnet']['attributes']['scope']:
            icon = '<span class="glyphicon glyphicon-resize-full"></span>&nbsp;'
        if instP_list[instP_dn, 'subnet'] == '':
            instP_list[instP_dn, 'subnet'] = icon + l3extSubnet['l3extSubnet']['attributes']['ip']
        else:
            instP_list[instP_dn, 'subnet'] = instP_list[instP_dn, 'subnet'] + '<br>' + icon + l3extSubnet['l3extSubnet']['attributes']['ip']

    # populate with consumed contract info
    fvRsCons_list = get_json(rest, '/api/class/fvRsCons.json?rsp-prop-include=naming-only&query-target-filter=wcard(fvRsCons.dn,"/out-")')['imdata']
    for fvRsCons in fvRsCons_list:
        instP_dn = str(fvRsCons['fvRsCons']['attributes']['dn']).split('/rscons-')[0]
        if instP_list[instP_dn, 'cons_ctrct'] == '':
            instP_list[instP_dn, 'cons_ctrct'] = fvRsCons['fvRsCons']['attributes']['tnVzBrCPName']
        else:
            instP_list[instP_dn, 'cons_ctrct'] = instP_list[instP_dn, 'cons_ctrct'] + '<br>' + fvRsCons['fvRsCons']['attributes']['tnVzBrCPName']

    # populate with consumed contract interface info
    fvRsConsIf_list = get_json(rest, '/api/class/fvRsConsIf.json?rsp-prop-include=naming-only&query-target-filter=wcard(fvRsConsIf.dn,"/out-")')['imdata']
    for fvRsConsIf in fvRsConsIf_list:
        instP_dn = str(fvRsConsIf['fvRsConsIf']['attributes']['dn']).split('/rsconsIf-')[0]
        if instP_list[instP_dn, 'cons_ctrct'] == '':
            instP_list[instP_dn, 'cons_ctrct'] = '<i>' + fvRsConsIf['fvRsConsIf']['attributes']['tnVzCPIfName'] + '</i>'
        else:
            instP_list[instP_dn, 'cons_ctrct'] = instP_list[instP_dn, 'cons_ctrct'] + '<br><i>' + fvRsConsIf['fvRsConsIf']['attributes']['tnVzCPIfName'] + '</i>'

    # populate with provided contract info
    fvRsProv_list = get_json(rest, '/api/class/fvRsProv.json?rsp-prop-include=naming-only&query-target-filter=wcard(fvRsProv.dn,"/out-")')['imdata']
    for fvRsProv in fvRsProv_list:
        instP_dn = str(fvRsProv['fvRsProv']['attributes']['dn']).split('/rsprov-')[0]
        if instP_list[instP_dn, 'prov_ctrct'] == '':
            instP_list[instP_dn, 'prov_ctrct'] = fvRsProv['fvRsProv']['attributes']['tnVzBrCPName']
        else:
            instP_list[instP_dn, 'prov_ctrct'] = instP_list[instP_dn, 'prov_ctrct'] + '<br>' + fvRsProv['fvRsProv']['attributes']['tnVzBrCPName']

    data = {}
    data['data'] = []
    for l3extInstP in l3extInstP_list:
        entry = []
        instP_dn = str(l3extInstP.dn)
        instP_url = apic_url + '/#bTenants:' + instP_list[instP_dn, 'tn'] + '|' + instP_dn
        entry.append(l3extInstP.name)
        entry.append('<a href="{}" target="_blank">{}</a>'.format(instP_url, l3extInstP.name))
        entry.append(instP_list[instP_dn, 'tn'])
        entry.append(ctx_list[l3extInstP.scope])
        entry.append(instP_list[instP_dn, 'l3out'])
        entry.append('<br>'.join(natsorted(instP_list[instP_dn, 'subnet'].split('<br>'))))
        entry.append('<br>'.join(natsorted(instP_list[instP_dn, 'cons_ctrct'].split('<br>'))))
        entry.append('<br>'.join(natsorted(instP_list[instP_dn, 'prov_ctrct'].split('<br>'))))
        data['data'].append(entry)
    print_data_table(save_table_data(data), 'hide_first_col')


def show_rule(md, nid, rest):
    from operator import itemgetter
    # Print SEC GRP rules in TCAM
    if nid is None:
        # Generate active node navbar
        nodes_new = {}
        nodes_rule_count = []
        fabricNode_list = md.lookupByClass('fabricNode')
        for node in fabricNode_list:
            # Skip APICs and unsupported switches
            if node.role != 'leaf' or node.fabricSt != 'active':
                continue
            nodes_new[node.id] = node
            path = '/api/mo/topology/pod-1/node-{}/sys/actrl.json?query-target=subtree&target-subtree-class=actrlRule&rsp-subtree-include=count'.format(node.id)
            nodes_rule_count.append(['{} ({})'.format(node.name, node.id), int(get_json(rest, path)['imdata'][0]['moCount']['attributes']['count'])])
        data = ''
        ids = []
        for id, node in sorted(nodes_new.items()):
            ids.append(id)
            node_url = 'http://' + re.sub(r'&nid.*$', "", URL) + '&nid=' + id
            data += '<li><a id="nid_{}" href="{}">{}</a></li>'.format(id, node_url, id)
        print '<h2 style="display:inline-block">Please select a node:</h2>'
        spinner(ids, 'show')
        node_dropdown = Template("""
        <div class="btn-group" style="position: relative; top: -5px; right: 0px;">
           <button type="button" class="btn btn-default">Node Id</button>
           <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
              <span class="caret"></span>
              <span class="sr-only">Toggle Dropdown</span>
           </button>
           <ul class="dropdown-menu" role="menu">
              @data
           </ul>
        </div>
        """)
        print node_dropdown.render(locals())
        # plot bar chart using google svc: https://google-developers.appspot.com/chart/
        chart_data = sorted(nodes_rule_count, key=itemgetter(1), reverse=True)
        chart_data.insert(0, ['Node Id', 'Rule Count'])
        chart_height = str(len(nodes_new) * 18 + 200) + 'px'
        bar_chart = Template("""
          <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
          <script type="text/javascript">
              google.charts.load('current', {'packages':['bar']});
              google.charts.setOnLoadCallback(drawStuff);

              function drawStuff() {
                var data = new google.visualization.arrayToDataTable(
                  @chart_data
                );

                var options = {
                  title: 'Node rule comsumption',
                  width: 900,
                  legend: { position: 'none' },
                  bars: 'horizontal', // Required for Material Bar Charts.
                  axes: {
                    x: {
                      0: { side: 'top', label: 'Rule Count'} // Top x-axis.
                    }
                  },
                  bar: { groupWidth: "90%" }
                };

                var chart = new google.charts.Bar(document.getElementById('chart_div'));
                chart.draw(data, options);
              };
          </script>
          <div id="chart_div" style="width: 900px; height: @chart_height;"></div>
        """)
        print bar_chart.render(locals())
    else:
        # print rules table header
        print '<h2>Node %s Rules</h2>' % nid
        print '''
        <table id="table_id" class="table table-striped table-bordered" cellspacing="0" width="100%">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>OperState</th>
                    <th>Scope</th>
                    <th>Type</th>
                    <th>Action</th>
                    <th>Direction</th>
                    <th>FilterId</th>
                    <th>SrcEPG / <i>L3out</i></th>
                    <th>DstEPG / <i>L3out</i></th>
                </tr>
            </thead>
        </table>
        '''
        ctx_name = {}   # construct context scope -> name mapping
        ctxs = md.lookupByClass('fvCtx')
        for ctx in ctxs:
            ctx_name[ctx.scope] = ctx.name

        vzFilter_name = {}   # construct filter id -> name mapping
        vzFilter_list = md.lookupByClass('vzFilter')
        for vzFilter in vzFilter_list:
            if vzFilter.fwdId not in vzFilter_name:
                vzFilter_name[vzFilter.fwdId] = vzFilter.name
            if vzFilter.revId not in vzFilter_name:
                vzFilter_name[vzFilter.revId] = vzFilter.name

        epg_name = {}   # construct epg pctag -> name mapping
        epgs = md.lookupByClass('fvAEPg')
        for epg in epgs:
            epg_tn = str(epg.dn).split('/')[1][3:]    # get parent tenant
            epg_ap = str(epg.dn).split('/')[2][3:]    # get parent ap
            epg_name[epg.scope, epg.pcTag] = epg_tn + '/' + epg_ap + '/' + epg.name

        l3extInstP_name = {}   # construct l3extInstP pctag -> name mapping
        l3extInstPs = md.lookupByClass('l3extInstP')
        for l3extInstP in l3extInstPs:
            l3extInstP_tn = str(l3extInstP.dn).split('/')[1][3:]    # get parent tenant
            l3extInstP_l3out = str(l3extInstP.dn).split('/')[2][4:]    # get parent l3out
            l3extInstP_name[l3extInstP.scope, l3extInstP.pcTag] = l3extInstP_tn + '/' + l3extInstP_l3out + '/' + l3extInstP.name

        actrlRules = md.lookupByClass('actrlRule', parentDn='topology/pod-1/node-{}/sys/actrl'.format(nid))
        data = {}
        data['data'] = []
        for rule in actrlRules:
            entry = []
            entry.append(rule.id)
            entry.append(rule.operSt)
            if rule.scopeId in ctx_name:
                entry.append(ctx_name[rule.scopeId])
            else:
                entry.append(rule.scopeId)
            entry.append(rule.type)
            entry.append(rule.action)
            entry.append(rule.direction)
            if rule.fltId in vzFilter_name:
                entry.append(vzFilter_name[rule.fltId])
            else:
                entry.append(rule.fltId)
            if (rule.scopeId, rule.sPcTag) in epg_name:
                entry.append(epg_name[rule.scopeId, rule.sPcTag])
            elif (rule.scopeId, rule.sPcTag) in l3extInstP_name:
                entry.append('<i>{}</i>'.format(l3extInstP_name[rule.scopeId, rule.sPcTag]))
            else:
                entry.append(rule.sPcTag)
            if (rule.scopeId, rule.dPcTag) in epg_name:
                entry.append(epg_name[rule.scopeId, rule.dPcTag])
            elif (rule.scopeId, rule.dPcTag) in l3extInstP_name:
                entry.append('<i>{}</i>'.format(l3extInstP_name[rule.scopeId, rule.dPcTag]))
            else:
                entry.append(rule.dPcTag)
            data['data'].append(entry)
        print_data_table(save_table_data(data))


def show_subnet(md):
    # Print the subnet list
    print '<h2>Subnet List</h2>'
    # print subnet info table header
    print '''
    <table id="table_id" class="table table-striped table-bordered" cellspacing="0" width="100%">
        <thead>
            <tr>
                <th>Subnet</th>
                <th>Tenant</th>
                <th>Bridge Domain</th>
                <th>Preferred</th>
                <th>Scope</th>
            </tr>
        </thead>
    </table>
    '''
    fvSubnet_list = md.lookupByClass('fvSubnet')
    data = {}
    data['data'] = []
    for fvSubnet in fvSubnet_list:
        entry = []
        tn = str(fvSubnet.dn).split('/')[1][3:]    # get parent tenant
        bd = str(fvSubnet.dn).split('/')[2][3:]    # get parent BD
        entry.append(fvSubnet.ip)
        entry.append(tn)
        entry.append(bd)
        entry.append(fvSubnet.preferred)
        entry.append('<br>'.join(fvSubnet.scope.split(',')))
        data['data'].append(entry)
    print_data_table(save_table_data(data))


def show_tenant(rest):
    # Print the tenant list
    print '<h2>Tenant List</h2>'
    # print tenant info table header
    print '''
    <table id="table_id" class="table table-striped table-bordered" cellspacing="0" width="100%">
        <thead>
            <tr>
                <th>Tenant</th>
                <th>Description</th>
                <th>BD Count</th>
                <th>Context Count</th>
                <th>Contract Count</th>
                <th>Filter Count</th>
                <th>EP Count</th>
                <th>EPG Count</th>
                <th>Imported Contract Count</th>
                <th>L4/L7 Graph Count</th>
            </tr>
        </thead>
    '''
    # populate per tenant class info
    class_list = ['fvBD', 'fvCtx', 'vzBrCP', 'vzFilter', 'fvCEp', 'fvAEPg', 'vzCPIf', 'vnsGraphInst']
    for cls in class_list:
        globals()['{}_list'.format(cls)] = {}
        if cls == 'fvCEp':
            pc, ps = get_page_info(rest, 'fvCEp')
            if pc > 1:
                json_data = get_json_parallel(rest, pc, ps, '/api/class/fvTenant.json?query-target=subtree&target-subtree-class=fvCEp&rsp-prop-include=naming-only&order-by=fvCEp.mac')
            else:
                json_data = get_json(rest, '/api/class/fvTenant.json?query-target=subtree&target-subtree-class={}&rsp-prop-include=naming-only'.format(cls))['imdata']
        else:
            json_data = get_json(rest, '/api/class/fvTenant.json?query-target=subtree&target-subtree-class={}&rsp-prop-include=naming-only'.format(cls))['imdata']
        for item in json_data:
            tn_dn = 'uni/' + str(item['{}'.format(cls)]['attributes']['dn']).split('/')[1]
            if tn_dn in globals()['{}_list'.format(cls)]:
                globals()['{}_list'.format(cls)][tn_dn] += 1
            else:
                globals()['{}_list'.format(cls)][tn_dn] = 1

    # print tenant info
    fvTenant_list = get_json(rest, '/api/class/fvTenant.json')['imdata']
    data = {}
    data['data'] = []
    for fvTenant in fvTenant_list:
        entry = []
        tn_dn = str(fvTenant['fvTenant']['attributes']['dn'])
        entry.append(fvTenant['fvTenant']['attributes']['name'])
        entry.append(fvTenant['fvTenant']['attributes']['descr'])
        for cls in class_list:
            count = 0
            if tn_dn in globals()['{}_list'.format(cls)]:
                count = globals()['{}_list'.format(cls)][tn_dn]
            entry.append(str(count))
        data['data'].append(entry)
    print_data_table(save_table_data(data))
    print '''
        <tfoot>
            <tr>
                <th></th>
                <th>Total</th>
    '''
    for cls in class_list:
        globals()['{}_count'.format(cls)] = sum(globals()['{}_list'.format(cls)].itervalues())
        print '<th>{}</th>'.format(globals()['{}_count'.format(cls)])
    print '''
            </tr>
        </tfoot>
    </table>
    '''


def stat_intf(session, nid, md):
    if nid is None:
        # Generate active node navbar
        pods = Pod.get(session)
        for pod in pods:
            nodes_new = {}
            fabricNode_list = md.lookupByClass('fabricNode')
            for node in fabricNode_list:
                # Skip APICs and unsupported switches
                if node.role == 'controller' or node.fabricSt != 'active':
                    continue
                nodes_new[node.id] = node
            data = ''
            ids = []
            for id, node in sorted(nodes_new.items()):
                ids.append(id)
                node_url = 'http://' + re.sub(r'&nid.*$', "", URL) + '&nid=' + id
                data = data + '<button type=\"button\" class=\"btn btn-default\" id=\"nid_' + id + '\" onclick=\"location.href=\"' + node_url + '\' \">' + id + '</button>'
            print '<h2>Please select a node:</h2>'
            spinner(ids, 'show')
            print '''<div class="btn-group" role="group" aria-label="...">'''
            print data
            print '''</div>'''
    else:
        # print interface table header
        print '<h2>Node %s Interface Utilization</h2>' % nid
        print '''
        <table id="table_id" class="table table-striped table-bordered" cellspacing="0" width="100%">
            <thead>
                <tr>
                    <th>Interface</th>
                    <th>Type</th>
                    <th>Admin State</th>
                    <th>Speed(bps)</th>
                    <th>Input pktsRate(pps)</th>
                    <th>Input util(%)</th>
                    <th>Output pktsRate(pps)</th>
                    <th>Output util(%)</th>
                </tr>
            </thead>
        </table>
        '''
        # Get 15min ingress stats for physical interfaces, and construct dict using intf dn as key
        eqptIngrTotal15min_list = md.lookupByClass('eqptIngrTotal15min', propFilter='wcard(eqptIngrTotal15min.dn,"topology/pod-1/node-{}/sys/phys")'.format(nid))
        eqptIngrTotal15min_dict = {}
        for eqptIngrTotal15min in eqptIngrTotal15min_list:
            eqptIngrTotal15min_dict[str(eqptIngrTotal15min.parentDn)] = eqptIngrTotal15min

        # Get 15min egress stats for physical interfaces, and construct dict using intf dn as key
        eqptEgrTotal15min_list = md.lookupByClass('eqptEgrTotal15min', propFilter='wcard(eqptEgrTotal15min.dn,"topology/pod-1/node-{}/sys/phys")'.format(nid))
        eqptEgrTotal15min_dict = {}
        for eqptEgrTotal15min in eqptEgrTotal15min_list:
            eqptEgrTotal15min_dict[str(eqptEgrTotal15min.parentDn)] = eqptEgrTotal15min

        # Get all physical interfaces
        intf_list = md.lookupByClass('l1PhysIf', parentDn='topology/pod-1/node-{}'.format(nid))
        data = {}
        data['data'] = []
        for intf in intf_list:
            if str(intf.dn) in eqptIngrTotal15min_dict:
                entry = []
                entry.append(intf.id)
                entry.append(intf.portT)
                entry.append(intf.adminSt)
                entry.append(intf.speed)
                entry.append(eqptIngrTotal15min_dict[str(intf.dn)].pktsRateAvg)
                entry.append(eqptIngrTotal15min_dict[str(intf.dn)].utilAvg)
                entry.append(eqptEgrTotal15min_dict[str(intf.dn)].pktsRateAvg)
                entry.append(eqptEgrTotal15min_dict[str(intf.dn)].utilAvg)
                data['data'].append(entry)
        print_data_table(save_table_data(data))


def find_dup_ip(rest):
    from collections import defaultdict
    # Print the endpoint list with dup ip
    print '<h2>Endpoints with Duplicate IP</h2>'
    # get fvCEp list
    pc, ps = get_page_info(rest, 'fvCEp')
    if pc > 1:
        fvCEp_list = get_json_parallel(rest, pc, ps, '/api/class/fvCEp.json?query-target-filter=ne(fvCEp.ip,"0.0.0.0")&order-by=fvCEp.mac')
    else:
        fvCEp_list = get_json(rest, '/api/class/fvCEp.json?query-target-filter=ne(fvCEp.ip,"0.0.0.0")')['imdata']

    dup_ep_dict = defaultdict(list)
    for fvCEp in fvCEp_list:
        dup_ep_dict[fvCEp['fvCEp']['attributes']['ip']].append(fvCEp)

    # populate with endpoint interface info
    fvCEp_if_list = {}
    if pc > 1:
        fvRsCEpToPathEp_list = get_json_parallel(rest, pc, ps, '/api/class/fvRsCEpToPathEp.json?order-by=fvRsCEpToPathEp.modTs')
    else:
        fvRsCEpToPathEp_list = get_json(rest, '/api/class/fvRsCEpToPathEp.json?rsp-prop-include=naming-only')['imdata']
    for fvRsCEpToPathEp in fvRsCEpToPathEp_list:
        fvCEp_dn = str(fvRsCEpToPathEp['fvRsCEpToPathEp']['attributes']['dn']).split('/rscEpToPathEp-')[0]
        if '/pathgrp-' in fvRsCEpToPathEp['fvRsCEpToPathEp']['attributes']['tDn']:
            intf = fvRsCEpToPathEp['fvRsCEpToPathEp']['attributes']['tDn'].split('/pathgrp-')[1][1:-1]
        else:
            match = re.match('topology/pod-(.*)/(prot)?paths-(.*)/pathep-\[(.*)]', str(fvRsCEpToPathEp['fvRsCEpToPathEp']['attributes']['tDn']))
            #intf = match.group(1) + '/' + match.group(3) + '/' + match.group(4) # get interface name
            intf = match.group(3) + '/' + match.group(4) # get interface name
        if fvCEp_dn in fvCEp_if_list:
            fvCEp_if_list[fvCEp_dn] = fvCEp_if_list[fvCEp_dn] + '<br>' + intf
        else:
            fvCEp_if_list[fvCEp_dn] = intf

    # print endpoint info table header
    print '''
    <table id="table_id" class="table table-striped table-bordered" cellspacing="0" width="100%">
        <thead>
            <tr>
                <th>IP Address</th>
                <th>MAC Address</th>
                <th>Interface</th>
                <th>Encap</th>
                <th>Learning Source</th>
                <th><i>EPG</i> / Port Group</th>
            </tr>
        </thead>
    </table>
    '''
    compEpPConn_list = {}
    for compEpPConn in get_json(rest, '/api/class/compEpPConn.json')['imdata']:
        if '/vnic-' in str(compEpPConn['compEpPConn']['attributes']['dn']):
            fvCEp_mac = str(compEpPConn['compEpPConn']['attributes']['dn']).split('/vnic-')[1][:17]
            compEpPConn_list[fvCEp_mac] = compEpPConn['compEpPConn']['attributes']['epgPKey']
    data = {}
    data['data'] = []
    for k, v in dup_ep_dict.items():
        if len(v) > 1:
            for fvCEp in v:
                entry = []
                fvCEp_dn = str(fvCEp['fvCEp']['attributes']['dn'])
                entry.append(fvCEp['fvCEp']['attributes']['ip'])
                entry.append(fvCEp['fvCEp']['attributes']['mac'])
                if fvCEp_dn in fvCEp_if_list:
                    entry.append('<br>'.join(natsorted(fvCEp_if_list[fvCEp_dn].split('<br>'))))
                else:
                    entry.append('&nbsp;')
                entry.append(fvCEp['fvCEp']['attributes']['encap'])
                entry.append(fvCEp['fvCEp']['attributes']['lcC'].replace(',', '<br>'))
                port_group = fvCEp_dn.split('/cep-')[0]
                if '/ldev-' in port_group or '/LDevInst-' in port_group:   # For ldev, find PG from vmnic
                    try:
                        port_group = compEpPConn_list[fvCEp_dn.split('/cep-')[1]]
                        tn = port_group.split('/')[1][3:]    # get tenant name
                        ap = port_group.split('/')[2][3:]    # get application profile name
                        epg = port_group.split('/')[3][4:]    # get epg name
                        port_group = '|'.join([tn, ap, epg])
                    except:
                        port_group = port_group.split('/LDevInst-')[0].split('/tn-')[1] + '/' + port_group.split('/LDevInst-')[1].replace('/G-', '/')
                else:
                    tn = port_group.split('/')[1][3:]    # get tenant name
                    ap = port_group.split('/')[2][3:]    # get application profile name
                    epg = port_group.split('/')[3][4:]    # get epg name
                    port_group = '|'.join([tn, ap, epg])
                if '[uni/' in port_group:
                    entry.append('<i>{}</i>'.format(port_group))
                else:
                    entry.append(port_group)
                data['data'].append(entry)
    print_data_table(save_table_data(data))


def flip_port(rest, session):
    from time import sleep
    import random
    form = cgi.FieldStorage()
    if form.getfirst("action") == '1':     # Flip port(s)
        print '''
        <div class="col-md-6">
          <div class="panel panel-info">
            <div class="panel-heading">Port Flipper</div>
            <div class="panel-body">
        '''
        if form.getlist("ports"):
            min = float(form.getfirst("min", 0))       # Get min timer, and set default to 0 sec
            max = float(form.getfirst("max", 1))       # Get max timer, and set default to 1 sec
            count = int(form.getfirst("count", 1))   # Get flip count, and set default to 1
            for loop in range(0, count):
                print "iteration {} of {}<br>".format(loop + 1, count)
                for port in form.getlist("ports"):
                    pod, node, card, port = port.split('/')
                    interface = Interface.get(session, pod, node, card, port)
                    tDn = "topology/pod-{}/paths-{}/pathep-[eth{}/{}]".format(pod, node, card, port)
                    if interface[0].adminstatus == 'up':
                        interface_disable(session, interface, tDn)
                    else:
                        interface_enable(session, interface, tDn)
                sleep(random.uniform(min, max))
            print 'Done'
        else:
            print '<span class=\"glyphicon glyphicon-remove-circle\" aria-hidden=\"true\"  style=\"font-size:2em; color:red\"></span> Port list can not be Null.'
        print '</div></div></div></div>'
    else:   # Show flip port page
        generate_page_common('Port Flipper')
        # Get all interfaces
        intfs = []
        for l1PhysIf in get_json(rest, '/api/class/l1PhysIf.json?rsp-prop-include=naming-only')['imdata']:
            pod = l1PhysIf['l1PhysIf']['attributes']['dn'].split('/')[1][4:]
            node = l1PhysIf['l1PhysIf']['attributes']['dn'].split('/')[2][5:]
            intf = l1PhysIf['l1PhysIf']['attributes']['id'][3:]
            intfs.append('/'.join([pod, node, intf]))
        intfs = natsorted(intfs)
        temp = Template("""
          <div class="form-group">
            <div class="col-sm-12">
              <select multiple="multiple" size="10" name="ports">
                #for @intf in @intfs:
                  <option value="@intf">Ethernet @intf</option>
                #end
              </select>
            </div>
          </div>
          <label class="control-label">Options</label><br>
          <div class="form-group">
            <label class="col-sm-1 control-label">Min</label>
            <div class="col-sm-3">
              <input type="number" class="form-control" name="min" placeholder="Default is 0 sec">
              <p class="help-block">Minimum wait time between flips</p>
            </div>
            <label class="col-sm-1 control-label">Max</label>
            <div class="col-sm-3">
              <input type="number" class="form-control" name="max" placeholder="Default is 1 sec">
              <p class="help-block">Maximum wait time between flips</p>
            </div>
            <label class="col-sm-1 control-label">Count</label>
            <div class="col-sm-3">
              <input type="number" class="form-control" name="count" placeholder="Default is 1">
              <p class="help-block">Total flips per port. Up/Down counted as 2 flips.</p>
            </div>
          </div>
          <input type="hidden" class="form-control" name="action" value="1">
          <div class="col-sm-12">
            <button type="submit" class="btn btn-primary pull-right">Start</button>
          </div>
         </form>
            <script>
            var flipper = $('select[name="ports"]').bootstrapDualListbox({
              nonSelectedListLabel: 'Available Ports',
              selectedListLabel: 'Selected Ports',
              preserveSelectionOnMove: 'moved',
              moveOnSelect: false,
              helperSelectNamePostfix: ''
            });
            </script>
         </div>
         </div>
        </div>
        """)
        print temp.render(locals())


# create xslt stylesheet to sort XML
def create_xslt_tmpl():
    xslt_tmpl = tempfile.NamedTemporaryFile()
    xslt_tmpl.write('''<?xml version="1.0" encoding="UTF-8"?>
    <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
        <xsl:strip-space elements="*"/>
        <!-- by default, copy all nodes -->
        <xsl:template match="@* | node()">
            <xsl:copy>
                <xsl:copy-of select="@*"/>
                <xsl:apply-templates select="node()">
                    <!-- sort elements by name -->
                    <xsl:sort select="name()"/>
                    <!-- for elements with same name, sort by attribute tDn -->
                    <xsl:sort select="@*[starts-with(name(), 'tDn')]"/>
                    <!-- for elements with same name, sort by attribute name -->
                    <xsl:sort select="@*[starts-with(name(), 'name')]"/>
                    <!-- for elements with same name, sort by attribute scope -->
                    <xsl:sort select="@*[starts-with(name(), 'scope')]"/>
                    <!-- for elements with same name, sort by attribute ending with Name -->
                    <xsl:sort select="@*[substring(name(), string-length(name()) - 3) = 'Name']"/>
                </xsl:apply-templates>
            </xsl:copy>
        </xsl:template>
    </xsl:stylesheet>''')
    xslt_tmpl.seek(0)
    return xslt_tmpl

# for XML files, sort and return;
# for tar.gz, first extract to tmp dir, then sort XML files
def xml_sort(f1, f2):
    tempfile.tempdir = '/var/www/html/tmp'
    if f1 != f2:    # check if src and dst files are same
        if os.path.exists(f1) and os.path.exists(f2):   # check if src/dst files exist
            if f1.endswith('xml') and f2.endswith('xml'):
                # src/dst files are both XML files
                xsltFile = create_xslt_tmpl()
                try:
                    for file in [f1, f2]:
                        # transform the xml with xslt template, which will sort element/attribute by names
                        subprocess.call("xsltproc -o {} {} {}".format(file, xsltFile.name, file), shell=True)
                        # format the xml for easy reading
                        subprocess.call("xmllint --format {} --output {}".format(file, file), shell=True)
                        # delete 1st line generated by xmllint
                        subprocess.call("sed -i 1d {}".format(file), shell=True)
                    return(f1, f2, 1, '')
                finally:
                    # Automatically cleans up the temp files after the diff terminates
                    xsltFile.close()
            elif f1.endswith('tar.gz') and f2.endswith('tar.gz'):
                # src/dst files are both tar.gz config files
                srcDir = tempfile.mkdtemp()
                dstDir = tempfile.mkdtemp()
                xsltFile = create_xslt_tmpl()
                try:
                    # untar the config files
                    subprocess.call("tar -xf {} -C {}".format(f1, srcDir), shell=True)
                    subprocess.call("tar -xf {} -C {}".format(f2, dstDir), shell=True)
                    for dir in [srcDir, dstDir]:
                        for tmp_file in glob.glob("{}/*.xml".format(dir)):
                            # rename files to match for both src/dst dirs
                            file = os.path.dirname(tmp_file) + '/' + os.path.basename(tmp_file).split('_')[-1]
                            os.rename(tmp_file, file)
                            # transform the xml with xslt template, which will sort element/attribute by names
                            subprocess.call("xsltproc -o {} {} {}".format(file, xsltFile.name, file), shell=True)
                            # format the xml for easy reading
                            subprocess.call("xmllint --format {} --output {}".format(file, file), shell=True)
                            # delete 1st line generated by xmllint
                            subprocess.call("sed -i 1d {}".format(file), shell=True)
                    return(srcDir, dstDir, 2, '')
                finally:
                    # Automatically cleans up the temp dir/files after the diff terminates
                    #shutil.rmtree(srcDir)
                    #shutil.rmtree(dstDir)
                    xsltFile.close()
            else:
                return('', '', 0, "Invalid combination of src/dst files")
        else:
            return('', '', 0, "Can't find src/dst files")
    else:
        return('', '', 0, "src/dst files are same")


def xml_diff(form):
    TMP_DIR = '/var/www/html/tmp/'
    WEB_TMP_DIR = '/tmp/'
    if form.getfirst("action") == 'upload':     # upload XML and do diff
        # A nested FieldStorage instance holds the file
        file1 = form['file1']
        # Save file #1
        if file1.filename:
            # strip leading path from file name to avoid directory traversal attacks
            sfile = TMP_DIR + os.path.basename(file1.filename)
            open(sfile, 'wb').write(file1.file.read())
        file2 = form['file2']
        # Save file #2
        if file2.filename:
            # strip leading path from file name to avoid directory traversal attacks
            dfile = TMP_DIR + os.path.basename(file2.filename)
            open(dfile, 'wb').write(file2.file.read())
        # extract tar.gz and transform/sort the XML files
        fh1, fh2, code, msg = xml_sort(sfile, dfile)
        if code == 0:   # xml diff error
            print("<h2>XML Configuration diff</h2><br><h4>{}</h4>".format(msg))
        elif code == 1: # compare xml
            fh1 = fh1[13:]  # relative path
            fh2 = fh2[13:]
            temp = Template("""
            <div class='page-header'>
              <div class='btn-toolbar pull-right'>
                <div class='btn-group'>
                  <button type='button' class='btn btn-default'><a onclick="$('#compare').mergely('scrollToDiff', 'prev');"><span class="glyphicon glyphicon-chevron-up"></span> Prev</a></button>
                  <button type='button' class='btn btn-default'><a onclick="$('#compare').mergely('scrollToDiff', 'next');"><span class="glyphicon glyphicon-chevron-down"></span> Next</a></button>
                  <button type='button' class='btn btn-default'><a onclick="$('#compare').mergely('swap');"><span class="glyphicon glyphicon-transfer"></span> Swap</a></button>
                </div>
              </div>
              <h2>XML Configuration diff</h2>
            </div>
            <div id="mergely-resizer">
                <div id="compare"></div>
            </div>
            <script type="text/javascript">
                $(document).ready(function () {
                    $('#compare').mergely({
                        width: 'auto',
                        height: 600,
                        cmsettings: {
                            mode: 'text/html',
                            readOnly: false, 
                            lineWrapping: true,
                        }
                    });
                    $.ajax({
                        type: 'GET', async: true, dataType: 'text',
                        url: '@fh1',
                        success: function (response) {
                            $('#compare').mergely('lhs', response);
                        }
                    });
                    $.ajax({
                        type: 'GET', async: true, dataType: 'text',
                        url: '@fh2',
                        success: function (response) {
                            $('#compare').mergely('rhs', response);
                        }
                    });
                });
            </script>
            """)
            print temp.render(locals())
        else:   # compare folder
            url = URL
            mismatch = []
            devnull = open('/dev/null', 'w')    # send diff output to /dev/null
            for file in glob.glob("{}/*.xml".format(fh1)):
                # compare each pair of xml files
                match = subprocess.call("diff {} {}".format(file, fh2 + '/' + os.path.basename(file)), stdout=devnull, shell=True)
                if match == 1:  #   files not match
                    mismatch.append(os.path.basename(file))
            mismatch = natsorted(mismatch)
            show_file = mismatch[0]
            dropdown_file_list = []
            for fn in mismatch:
                dropdown_file_list.append('<li><a href="http://{}&action=show&fh1={}&fh2={}&xmlf={}">{} ({})</a></li>'.format(url, fh1[len(TMP_DIR):], fh2[len(TMP_DIR):], fn, fn, os.path.getsize(fh1 + '/' + fn)))
            fh1 = WEB_TMP_DIR + fh1[len(TMP_DIR):]
            fh2 = WEB_TMP_DIR + fh2[len(TMP_DIR):]
            temp = Template("""
            <div class='page-header'>
              <div class='btn-toolbar pull-right'>
                <div class='btn-group'>
                  <div class="btn-group" role="group">
                    <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                      Select XML File
                      <span class="caret"></span>
                    </button>
                    <ul class="dropdown-menu">
                      #for @item in @dropdown_file_list:
                        @item
                      #end
                    </ul>
                  </div>                
                  <button type='button' class='btn btn-default'><a onclick="$('#compare').mergely('scrollToDiff', 'prev');"><span class="glyphicon glyphicon-chevron-up"></span> Prev</a></button>
                  <button type='button' class='btn btn-default'><a onclick="$('#compare').mergely('scrollToDiff', 'next');"><span class="glyphicon glyphicon-chevron-down"></span> Next</a></button>
                  <button type='button' class='btn btn-default'><a onclick="$('#compare').mergely('swap');"><span class="glyphicon glyphicon-transfer"></span> Swap</a></button>
                </div>
              </div>
              <h2>XML Configuration diff</h2>
            </div>
            <div id="mergely-resizer">
                <div id="compare"></div>
            </div>
            <script type="text/javascript">
                $(document).ready(function () {
                    $('#compare').mergely({
                        width: 'auto',
                        height: 600,
                        cmsettings: {
                            mode: 'text/html',
                            readOnly: false, 
                            lineWrapping: true,
                        }
                    });
                    $.ajax({
                        type: 'GET', async: true, dataType: 'text',
                        url: '@fh1/@show_file',
                        success: function (response) {
                            $('#compare').mergely('lhs', response);
                        }
                    });
                    $.ajax({
                        type: 'GET', async: true, dataType: 'text',
                        url: '@fh2/@show_file',
                        success: function (response) {
                            $('#compare').mergely('rhs', response);
                        }
                    });
                });
            </script>
            """)
            print temp.render(locals())
    elif form.getfirst("action") == 'show':  # show xml diff
        url = URL.split('&action')[0]   # trim extra params when user choose a new xml in the dropdown
        fh1 = TMP_DIR + form.getfirst("fh1")
        fh2 = TMP_DIR + form.getfirst("fh2")
        mismatch = []
        devnull = open('/dev/null', 'w')    # send diff output to /dev/null
        for file in glob.glob("{}/*.xml".format(fh1)):
            # compare each pair of xml files
            match = subprocess.call("diff {} {}".format(file, fh2 + '/' + os.path.basename(file)), stdout=devnull, shell=True)
            if match == 1:  #   files not match
                mismatch.append(os.path.basename(file))
        mismatch = natsorted(mismatch)
        show_file = form.getfirst("xmlf")
        dropdown_file_list = []
        for fn in mismatch:
            dropdown_file_list.append('<li><a href="http://{}&action=show&fh1={}&fh2={}&xmlf={}">{} ({})</a></li>'.format(url, fh1[len(TMP_DIR):], fh2[len(TMP_DIR):], fn, fn, os.path.getsize(fh1 + '/' + fn)))
        fh1 = WEB_TMP_DIR + fh1[len(TMP_DIR):]
        fh2 = WEB_TMP_DIR + fh2[len(TMP_DIR):]
        temp = Template("""
        <div class='page-header'>
          <div class='btn-toolbar pull-right'>
            <div class='btn-group'>
              <div class="btn-group" role="group">
                <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                  Select XML File
                  <span class="caret"></span>
                </button>
                <ul class="dropdown-menu">
                  #for @item in @dropdown_file_list:
                    @item
                  #end
                </ul>
              </div>                
              <button type='button' class='btn btn-default'><a onclick="$('#compare').mergely('scrollToDiff', 'prev');"><span class="glyphicon glyphicon-chevron-up"></span> Prev</a></button>
              <button type='button' class='btn btn-default'><a onclick="$('#compare').mergely('scrollToDiff', 'next');"><span class="glyphicon glyphicon-chevron-down"></span> Next</a></button>
              <button type='button' class='btn btn-default'><a onclick="$('#compare').mergely('swap');"><span class="glyphicon glyphicon-transfer"></span> Swap</a></button>
            </div>
          </div>
          <h2>XML Configuration diff</h2>
        </div>
        <div id="mergely-resizer">
            <div id="compare"></div>
        </div>
        <script type="text/javascript">
            $(document).ready(function () {
                $('#compare').mergely({
                    width: 'auto',
                    height: 600,
                    cmsettings: {
                        mode: 'text/html',
                        readOnly: false, 
                        lineWrapping: true,
                    }
                });
                $.ajax({
                    type: 'GET', async: true, dataType: 'text',
                    url: '@fh1/@show_file',
                    success: function (response) {
                        $('#compare').mergely('lhs', response);
                    }
                });
                $.ajax({
                    type: 'GET', async: true, dataType: 'text',
                    url: '@fh2/@show_file',
                    success: function (response) {
                        $('#compare').mergely('rhs', response);
                    }
                });
            });
        </script>
        """)
        print temp.render(locals())
    else:    # Show xml upload page
        url = 'http://' + URL
        action_url = url.split('?')[0]
        param = []
        for pair in url.split('?')[1].split('&'):
            name, value = pair.split('=')
            list = []
            list.append(name)
            list.append(urllib.unquote(value).decode('utf8'))
            param.append(list)
        params = []
        for param_name, param_value in param:
            params.append('<input type="hidden" class="form-control" name="{}" value="{}">'.format(param_name, param_value))
        temp = Template("""
        <div class="col-md-6">
          <div class="panel panel-info">
            <div class="panel-heading">XML diff</div>
            <div class="panel-body">
                <form class="form-horizontal" role="form" action="@action_url" method="POST" enctype="multipart/form-data" onSubmit="document.getElementById('submit').disabled=true;">
                    #for @p in @params:
                        @p
                    #end
                    <p>
                        <h4>Notes</h4><br>
                        <li>The tool compares XML, and ignores the order of all element/attribute.</li>
                        <li>Elements will be sorted first by their names.</li>
                        <li>When more than one element has the same name, attributes like <strong>name</strong>, <strong>tDn</strong> etc. will be used to break tie.</li>
                        <li>XML files or config (<strong>*.tar.gz</strong>) exported from APIC in XML format are accepted.</li>
                        <li>Only XML config of APICs are processed, files under /dhcpconfig or /idconfig are not.</li>
                        <li>With 2 XML files as input, diff will show on the next page.</li>
                        <li>With tar.gz config files, only different files are shown, and the first file is shown by default.</li>
                        <li>Uploaded files will be purged automatically daily.</li>
                    </p><br>
                    <div class="form-group">
                        <label class="col-sm-2 control-label">Source File 1</label>
                        <div class="col-sm-9">
                            <div class="fileinput input-group fileinput-new" data-provides="fileinput">
                                <div class="form-control" data-trigger="fileinput">
                                    <i class="glyphicon glyphicon-file fileinput-exists"></i>
                                    <span class="fileinput-filename"></span></div>
                                <span class="input-group-addon btn btn-default btn-file">
                                    <span class="fileinput-new">Browse</span>
                                    <span class="fileinput-exists">Change</span>
                                    <input type="hidden" value="" name="">
                                    <input type="file" name="file1"></span>
                                <a href="#" class="input-group-addon btn btn-default fileinput-exists" data-dismiss="fileinput">Remove</a>
                            </div>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="col-sm-2 control-label">Source File 2</label>
                        <div class="col-sm-9">
                            <div class="fileinput input-group fileinput-new" data-provides="fileinput">
                                <div class="form-control" data-trigger="fileinput">
                                    <i class="glyphicon glyphicon-file fileinput-exists"></i>
                                    <span class="fileinput-filename"></span></div>
                                <span class="input-group-addon btn btn-default btn-file">
                                    <span class="fileinput-new">Browse</span>
                                    <span class="fileinput-exists">Change</span>
                                    <input type="hidden" value="" name="">
                                    <input type="file" name="file2"></span>
                                <a href="#" class="input-group-addon btn btn-default fileinput-exists" data-dismiss="fileinput">Remove</a>
                            </div>
                        </div>
                    </div>
                    <input type="hidden" class="form-control" name="action" value="upload">
                    <div class="col-sm-12">
                    <button type="submit" class="btn btn-primary pull-right" id="submit">Compare</button>
                    </div>
                </form>
            </div>
          </div>
        </div>
        """)
        print temp.render(locals())


def cobra_login(apic_url, USER, PASS):
    """login to apic with Cobra SDK.

    Args:
        apic_url: The URL to access apic.
        USER: apic user name.
        PASS: apic password.

    Returns:
        md: MoDirectory
    """    
    import cobra.mit.access
    import cobra.mit.request
    import cobra.mit.session

    ls = cobra.mit.session.LoginSession(apic_url, USER, PASS)
    md = cobra.mit.access.MoDirectory(ls)
    md.login()
    return md


def main():
    form = cgi.FieldStorage()

    # Get the form value associated with input name 'apic_ip'.
    APIC = form.getfirst("apic_ip")

    # Get the form value associated with input name 'user'.
    # Use default "admin" if there is none.
    USER = form.getfirst("user", "admin")

    # Get the form value associated with input name 'pwd'.
    PASS = base64.b64decode(form.getfirst("pwd"))

    # Log into APIC and create a directory object
    apic_url = "https://" + APIC
    session = Session(apic_url, USER, PASS, False)
    resp = session.login()
    if not resp.ok:
        print '%% Could not login to APIC'
        sys.exit(0)

    print_html_header()
    print_navbar(APIC, USER, PASS)

    # Get the page name from query URL.
    pname = form.getfirst("pname")
    if pname == 'create_tn':
        # Show the create tenant page
        create_tn(session)
    elif pname == 'delete_tn':
        # Show the delete tenant page
        rest = rest_login(APIC, USER, PASS)
        delete_tn(rest, session)
    elif pname == 'show_apic':
        # Show the APIC list
        md = cobra_login(apic_url, USER, PASS)
        show_apic(md)
    elif pname == 'show_switch':
        # Show the switch list
        md = cobra_login(apic_url, USER, PASS)
        show_switch(md)
    elif pname == 'show_ctrct':
        # Show the Contract list
        md = cobra_login(apic_url, USER, PASS)
        rest = rest_login(APIC, USER, PASS)
        show_ctrct(apic_url, md, rest)
    elif pname == 'show_ctrct_detail':
        # Show the detail Contract list
        md = cobra_login(apic_url, USER, PASS)
        rest = rest_login(APIC, USER, PASS)
        show_ctrct_detail(apic_url, md, rest)
    elif pname == 'show_ep':
        # Show the endpoint list
        rest = rest_login(APIC, USER, PASS)
        show_ep(rest)
    elif pname == 'show_epg':
        # Show the EPG list
        rest = rest_login(APIC, USER, PASS)
        show_epg(apic_url, rest)
    elif pname == 'show_instP':
        # Show the L3 External Network Instance Profile list
        md = cobra_login(apic_url, USER, PASS)
        rest = rest_login(APIC, USER, PASS)
        show_instP(apic_url, md, rest)
    elif pname == 'show_rule':
        # Show TCAM rules
        nid = form.getfirst("nid")
        md = cobra_login(apic_url, USER, PASS)
        rest = rest_login(APIC, USER, PASS)
        show_rule(md, nid, rest)
    elif pname == 'show_subnet':
        # Show the subnet list
        md = cobra_login(apic_url, USER, PASS)
        show_subnet(md)
    elif pname == 'show_tenant':
        # Show the tenant list
        rest = rest_login(APIC, USER, PASS)
        show_tenant(rest)
    elif pname == 'stat_intf':
        # Show the interface utilization page
        # Get the node id from query URL.
        nid = form.getfirst("nid")
        md = cobra_login(apic_url, USER, PASS)
        stat_intf(session, nid, md)
    elif pname == 'find_dup_ip':
        # Show the find ep with dup ip page
        rest = rest_login(APIC, USER, PASS)
        find_dup_ip(rest)
    elif pname == 'flip_port':
        # Show the port flip page
        rest = rest_login(APIC, USER, PASS)
        flip_port(rest, session)
    elif pname == 'xml_diff':
        # Show the xml diff page
        xml_diff(form)
    else:
        # Show the dashboard
        rest = rest_login(APIC, USER, PASS)
        show_dashboard(rest)
    print '</div></body></html>'

try:
    print("Content-type: text/html\n\n")   # generating html
    main()
except:
    cgi.print_exception()                 # catch and print errors
