let ip_to_back = location.host
sessionStorage.setItem('sortOrder',JSON.stringify(Array()))
let dbSelector = document.getElementById('db-selector')
let search = document.getElementById('search')
const import_btn = document.getElementById('import_btn_local')
const export_btn = document.getElementById('export_btn_local')


async function get_modem_data(){
    const myInit = {
        method: "GET",
        headers: {
            Accept: "application/json",
        },
        mode: "cors",
        cache: "default",
    };
    const data = await fetch(`http://${ip_to_back}/get_modem_data`,myInit)
    return data
}
async function get_signal_data(){
    const myInit = {
        method: "GET",
        headers: {
            Accept: "application/json",
        },
        mode: "cors",
        cache: "default",
    };
    const data = await fetch(`http://${ip_to_back}/get_data`,myInit)
    return data
}

function drawData(e){
    let key = e.target.parentElement.id
    let data = JSON.parse(sessionStorage.getItem(key))
    let dataDiv = document.getElementById('data_window')
    dataDiv.innerHTML = ''

    let title = document.createElement('h3')
    title.innerHTML = key

    let dataP = document.createElement('pre')
    dataP.innerHTML = JSON.stringify(data,undefined,4)
    dataP.style.width='800px'
    dataP.style.height='800px'
    dataP.classList.add('overflow-auto')

    dataDiv.append(title)
    dataDiv.append(dataP)
    

}



function drawIndex(){
    let db_type = document.getElementById('db-selector').value
    let searchStr = document.getElementById('search').value
    let table = document.getElementById(db_type)
    let sigtable = document.getElementById('signal')
    let nettable = document.getElementById('network')
    sigtable.parentElement.parentElement.hidden=true
    nettable.parentElement.parentElement.hidden=true
    table.parentElement.parentElement.hidden=false
    const entries = new Array()


    for (let i = 0; i<sessionStorage.length;i++){
        let key = sessionStorage.key(i)
        if (db_type=='signal'){
            if (key=='sortOrder' || key.includes('.')){
                continue
            }
            
        }else{
            if (key=='sortOrder' || !key.includes('.')){
                continue
            }
        }

        let entry = JSON.parse(sessionStorage.getItem(key))
        entries.push(entry)
    }

    let filterdEntries =  entries.filter((entries) => {
        let cond = matchSearch(true,searchStr,entries)
        return cond
    })

    table.innerHTML = ""   
    filterdEntries.forEach((entry)=>{

        let row = document.createElement('tr')
        let entryMarker = document.createElement('td')
        let entry_name = document.createElement('td')
        entryMarker.setAttribute('scope','row')
        
        
        if (db_type=='signal'){
            row.id = entry.cog_id
            entryMarker.innerHTML = entry.cog_id
            entry_name.append(entry.name)
        } else {
            row.id = entry.ip
            entryMarker.innerHTML = entry.ip
            entry_name.append(entry.intersection)
        }
        row.addEventListener('click',drawData)
        row.append(entryMarker)
        row.append(entry_name)

        table.append(row)
    })
}

function matchSearch(cond,searchStr,entry){
    cond = cond && (
        entry?.intersection?.toLocaleLowerCase('en-US')?.includes(searchStr.toLocaleLowerCase('en-US')) 
        || entry?.name?.toLocaleLowerCase('en-US')?.includes(searchStr.toLocaleLowerCase('en-US')) 
        || String(entry?.cog_id)?.includes(searchStr) 
        || entry.ip.includes(searchStr) 
    )
    return cond
}

function drawGuide(guide,parent,elementType){
    guide.forEach((column)=>{
        let td = document.createElement(elementType)
        let i =0
        for (elem of column.elements){
            if (elem.includes('text:')){
                td.append(elem.slice(5,-1))
                i++
                continue
            }
            tempElem = document.createElement(elem)
            let keys = Object.keys(column.attributes[i])
            let atts = column.attributes[i]
            for (let key of keys){
                tempElem.setAttribute(key,atts[key])
            }
            keys = Object.keys(column.styles[i])
            atts = column.styles[i]
            for (let key of keys){
                tempElem.style[key]=atts[key]
            }

            for (let cla of column.classes[i]){
                tempElem.classList.add(cla)
            }
            for (let listener of column.listeners[i]){
                tempElem.addEventListener('input',listener)
            }
            tempElem.id=column.ids[i]
            td.append(tempElem)
            i++
        }
        parent.append(td)
    })
}

function drawExportOptions(fields){
        let table = document.getElementById('local-export-options')
        let saveButton = document.getElementById('local-export-button')
        let checkbox = document.createElement('div')
        saveButton.disabled=false
    
        let guide = [
            {
                elements:[],
                attributes:[],
                classes:[],
                styles:[],
                ids:[],
                listeners:[]
            },
            {
                elements:['input'],
                attributes:[{type:'text',placeholder:'name'}],
                classes:[['form-control-sm']],
                styles:[{width:'100px'}],
                ids:[`name-${ind}`],
                listeners:[[]]
            },
            {
                elements:['input','-','input'],
                attributes:[{type:'text',placeholder:'start port'},{},{type:'text',placeholder:'end port'}],
                classes:[['form-control-sm'],[],['form-control-sm']],
                styles:[{width:'80px'},{},{width:'80px'}],
                ids:[`int_port_start-${ind}`,'',`int_port_end-${ind}`],
                listeners:[[wan_input],[],[wan_input]]
            },
            {
                elements:['input',':','input','-','span'],
                attributes:[{type:'text',placeholder:'ip'},{},{type:'text',placeholder:'start lan port'},{},{}],
                classes:[['form-control-sm'],[],['form-control-sm'],[],[]],
                styles:[{width:'100px'},{},{width:'80px'},{},{}],
                ids:[`ip_loc-${ind}`,'',`loc_port-${ind}`,'',`link+${ind}`],
                listeners:[[],[],[lan_input],[],[]]
            },        
            {
                elements:['input'],
                attributes:[{type:'text',placeholder:'tcp,udp,or both'}],
                classes:[['form-control-sm']],
                styles:[{width:'140px'}],
                ids:[`protocol-${ind}`],
                listeners:[[]]
            },
            {
                elements:['input'],
                attributes:[{type:'text',placeholder:'true/false,0/1'}],
                classes:[['form-control-sm']],
                styles:[{width:'100px'}],
                ids:[`enable-${ind}`],
                listeners:[[]]
            },
        ]
        drawGuide(guide,checkbox,'div')
        
}

export_btn.addEventListener('click',async e=>{
    const myInit = {
        method: "POST",
        mode: "cors",
        cache: "default",
        headers: {'Content-Type': 'application/json'},
        body:JSON.stringify({
            signals:['cog_id','ip','online_status']
        })
    };
    let db_type = document.getElementById('db-selector').value
    let url = `http://${ip_to_back}/get_xlsx?`+ new URLSearchParams({type:db_type})
    let data = await fetch(url,myInit)
    let a = document.createElement('a')
    let data_b = await data.blob()
    url = URL.createObjectURL(data_b)
    a.href = url
    a.download = `${db_type}.xlsx`
    document.body.appendChild(a)
    a.click()
    setTimeout(()=>{
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }, 0);
})

import_btn.addEventListener('click',async e=>{
    let db_type = document.getElementById('db-selector').value
    let file = document.createElement('input')
    file.setAttribute('type','file')
    file.display = 'hidden'
    document.body.appendChild(file)
    file.addEventListener('change', async (e) => {
        if (e.target.files[0]) {
            let data = new FormData()
            let filedata = e.target.files[0]
            data.append('file', filedata)
            console.log('You selected ' + e.target.files[0].name);
            
            const myInit = {
                method: "POST",
                body: data,
                mode: "cors",
                cache: "default",
                redirect: 'follow'
            };
            let res = await fetch(`http://${ip_to_back}/post_xlsx?type=${db_type}`,myInit)
            location.reload()
        }

    })
    file.click()



})


search.addEventListener('input',drawIndex)
dbSelector.addEventListener('input',drawIndex)
addEventListener("load",async (event) =>  {

    const sig_data = await get_signal_data()
    const net_data = await get_modem_data()
    d_json = await sig_data.json()
    d_json.forEach(signal => {
        sessionStorage.setItem(signal.cog_id,JSON.stringify(signal))

    });
    d_json = await net_data.json()
    d_json.forEach(signal => {
        sessionStorage.setItem(signal.ip,JSON.stringify(signal))

    });
})
