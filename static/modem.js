let ip = location.host
let filters = document.getElementById('filters')
let searchBox = document.getElementById('search')
let columnHeaders = document.getElementById('headers')
let saveButton = document.getElementById('sv-btn')
let filterList = document.getElementById('filter-list')
let confDial = document.getElementById('conf')
let data_table = document.getElementById('list')
let addButton = document.getElementById('add-btn')
sessionStorage.setItem('sortOrder',JSON.stringify(Array()))

const export_btn = document.getElementById('export_btn')
const import_btn = document.getElementById('import_btn')

async function get_data(){
    const myInit = {
        method: "GET",
        headers: {
            Accept: "application/json",
        },
        mode: "cors",
        cache: "default",
    };
    const data = await fetch(`http://${ip}/get_modem_data`,myInit)
    console.log(data)
    return data
}

function filterState(e){
    let filters = document.getElementById('filters')
    Array.from(filters.children).forEach( (filter)=>{
        filter.firstElementChild.classList.remove('active')
    })
    e.target.classList.add("active")
}

function getFilter(){
    let baseFilters = document.getElementById('filters')
    let filters = {}
    Array.from(baseFilters.children).forEach( (filter)=>{
        if (filter.firstElementChild.classList.contains('active')){
            filters['baseFilter']=filter.firstElementChild.id
        }
    })
    return filters
}

function matchSearch(cond,searchStr,signal){
    cond = cond && (
        signal?.intersection?.toLocaleLowerCase('en-US')?.includes(searchStr.toLocaleLowerCase('en-US')) 
        || String(signal?.cog_id)?.includes(searchStr) 
        || signal.ip.includes(searchStr) 
        || String(signal?.modem?.model)?.includes(searchStr)
        || String(signal?.modem?.sn)?.includes(searchStr)
        || String(signal?.modem?.os_ver)?.includes(searchStr)
        || String(signal?.modem?.fw_ver)?.includes(searchStr)
    )
    return cond
}

const finder = (obj, keys, index = 0) => {
    const result = obj[keys[index++]];
    
    if (!result) {
        return obj;
    }
    return finder(result, keys, index);
}

function getSortFunction(){
    let keyIdMap = {
        cog_id:['cog_id'],
        name:['intersection'],
        type:['modem','model'],
        IP:['ip'],
        sn:['modem','sn'],
        os:['modem','os_ver'],
        firm:['modem','fw_ver'],
        temp:['modem','temp'],
        sig:['modem','dbm'],
        cpu:['modem','cpu'],
        reg:['modem','upgradable'],
    }
    let sortOrder = JSON.parse(sessionStorage.getItem('sortOrder'))
    funcArray = Array()
    for (let i = 0;i<sortOrder.length;i++){
        let elem = document.getElementById(sortOrder[i])
        let dir
        if (elem.classList.contains('sort-up')){
            dir = 1
        } else {
            dir = -1
        }
        sortFunc_i = (a,b) =>{
            let trueA = finder(a,keyIdMap[elem.id])
            let trueB = finder(b,keyIdMap[elem.id])
            if (!(typeof trueA === 'string')){
                if (!(typeof trueA === 'boolean')){
                    trueA = String(trueA).padStart(String(trueB).length,'0')

                }else{
                    trueA = String(trueA)
                }
            }
            if (!(typeof trueB === 'string')){
                if (!(typeof trueB === 'boolean')){
                    trueB = String(trueB).padStart(String(trueA).length,'0')
                } else {
                    trueB = String(trueB)
                }
            }
            return trueA.localeCompare(trueB)*(dir)
        }
        funcArray.push(sortFunc_i)
    }
    sortFunc = (a,b)=>{
        for (let i=0;i<funcArray.length;i++){
            let cond = funcArray[i](a,b)
            if (cond!=0 || i==funcArray.length-1){
                return cond
            }
        }
    }
    return sortFunc
}

function drawTable(filters){
    let allSignalCount = 0
    let count600 = 0
    let count1150 = 0
    let count900 = 0
    let allIpCount = 0
    let noneCount = 0
    let gpsCount = 0
    let noGpsCount = 0
    const signals = new Array()
    let searchStr = document.getElementById('search').value

    for (let i = 0; i<sessionStorage.length;i++){
        let ip = sessionStorage.key(i)
        if (ip=='sortOrder' || !ip.includes('.')){
            continue
        }
        allIpCount++
        let signal = JSON.parse(sessionStorage.getItem(ip))

        let filt1 = signal.modem?.model?.includes('600LE')
        let filt2 = signal.modem?.model?.includes('1150')
        let filt3 = signal.modem?.model?.includes('900')
        if (filt1){
            count600++
        }
        if (filt2){
            count1150++
        }
        if (filt3){
            count900++
        }
        if (!(filt1||filt2||filt3)){
            noneCount++
        } else{
            allSignalCount++
        }

        if (signal.modem?.lat!=0 && signal.modem?.lat!=undefined){
            gpsCount++
        }else{
            noGpsCount++
        }
        signals.push(signal)
    }

    let aCountElem = document.getElementById("all-signal-count")
    let count900Elem = document.getElementById("900-count")
    let count1150Elem = document.getElementById("1150-count")
    let count600Elem = document.getElementById("600-count")
    let noCountElem = document.getElementById("no-count")
    let yesCountElem = document.getElementById("yes-count")
    let gpsCountElem = document.getElementById("gps-count")
    let noGpsCountElem = document.getElementById("no-gps-count")

    aCountElem.innerHTML = `( ${allIpCount} )`
    count900Elem.innerHTML = `( ${count900} )`
    count1150Elem.innerHTML = `( ${count1150} )`
    count600Elem.innerHTML = `( ${count600} )`
    noCountElem.innerHTML = `( ${noneCount} )`
    yesCountElem.innerHTML = `( ${allSignalCount} )`
    gpsCountElem.innerHTML = `( ${gpsCount} )`
    noGpsCountElem.innerHTML = `( ${noGpsCount} )`

    let filterdSignals = new Array()
    if (filters.baseFilter =="600-filter"){
        filterdSignals = signals.filter((signal) => {
            let cond = signal.modem?.model?.includes('600LE')
            cond = matchSearch(cond,searchStr,signal)
            return cond
        })
    }
    if (filters.baseFilter =="1150-filter"){
        filterdSignals = signals.filter((signal) => {
            let cond = signal.modem?.model?.includes('1150')
            cond = matchSearch(cond,searchStr,signal)
            
            return cond
        })
        
    }
    if (filters.baseFilter =="900-filter"){
        filterdSignals = signals.filter((signal) => {
            let cond = signal.modem?.model?.includes('900')

            cond = matchSearch(cond,searchStr,signal)
            return cond
        })
    } 
    if (filters.baseFilter =="no-filter"){
        filterdSignals = signals.filter((signal) => {
            let cond = signal.modem?.model?.includes('600LE')
            cond = signal.modem?.model?.includes('1150') ||cond
            cond = signal.modem?.model?.includes('900')|| cond
            cond = !cond
            cond = matchSearch(cond,searchStr,signal)
            return cond
        })
    } 
    if (filters.baseFilter =="yes-filter"){
        filterdSignals = signals.filter((signal) => {
            let cond = signal.modem?.model?.includes('600LE')
            cond = signal.modem?.model?.includes('1150') ||cond
            cond = signal.modem?.model?.includes('900')|| cond
            cond = matchSearch(cond,searchStr,signal)
            return cond
        })
    } 
    if (filters.baseFilter =="all-signal-filter"){
        // make sure this one is getting hit
        filterdSignals =  signals.filter((signal) => {
            let cond = matchSearch(true,searchStr,signal)
            return cond
        })
    }
    if (filters.baseFilter =="gps-filter"){
        // make sure this one is getting hit
        filterdSignals =  signals.filter((signal) => {
            let cond = signal.modem?.lat!=0 && signal.modem?.lat!=undefined
            cond = matchSearch(cond,searchStr,signal)
            return cond
        })
    }
    if (filters.baseFilter =="no-gps-filter"){
        // make sure this one is getting hit
        filterdSignals =  signals.filter((signal) => {
            let cond = !(signal.modem?.lat!=0 &&signal.modem?.lat!=undefined)
            cond = matchSearch(cond,searchStr,signal)
            return cond
        })
    }

    filterdSignals.sort(getSortFunction())
    const table_data = document.getElementById('list')

    table_data.innerHTML = ""    
    let alarms = [
        {
            name:'license',
            symbol:'&#x1F4B2;',
            condition: (signal)=>{return signal?.modem?.licenses?.length <1},
            title:'License Expired'
        },
        {
            name:'modem',
            symbol:'&#x1F4F6;',
            condition: (signal)=>{return !signal?.modem?.os_ver},
            title:'No Modem'
        },
        {
            name:'gps',
            symbol:'&#x1F4CD;',
            condition: (signal)=>{return signal?.modem?.lon==0},
            title:'No GPS'
        },
        {
            name:'upgrade',
            symbol:'&#x1F53C;',
            condition: (signal)=>{return signal?.modem?.upgradeable},
            title:'VZ Firmware Upgrade Available'
        },
    ]
    filterdSignals.forEach((signal)=>{

        let entry = document.createElement('tr')
        entry.id = signal.ip



        let chkBox = document.createElement('th')
        let chkBoxInp = document.createElement('input')
        chkBoxInp.setAttribute('type','checkbox')
        chkBox.append(chkBoxInp)
        entry.append(chkBox)

        let ip_loc = document.createElement('th')
        ip_loc.setAttribute('scope','row')
        ip_loc.innerHTML = signal.ip
        entry.append(ip_loc)

        let entry_name = document.createElement('td')
        entry_name.append(signal.intersection)
        
        for (let alarm of alarms){
            if (alarm.condition(signal)){
                entry.setAttribute(`data-${alarm.name}`,alarm.symbol)
                alarm.elem = document.createElement('span')
                alarm.elem.innerHTML = '['+alarm.symbol+']'
                alarm.elem.setAttribute('title',alarm.title)
                alarm.elem.style.width= '30px'
                alarm.elem.style.cursor= 'pointer'
                entry_name.append(alarm.elem)
            }
        }

        entry.append(entry_name)

        let cogId = document.createElement('td')
        cogId.innerHTML = signal.cog_id
        entry.append(cogId)
            
        let type = document.createElement('td')
        type.innerHTML = signal.modem?.model
        entry.append(type)

        let sn = document.createElement('td')
        sn.innerHTML = signal.modem?.sn
        entry.append(sn)

        let os = document.createElement('td')
        os.innerHTML = signal.modem?.os_ver
        entry.append(os)

        let fw = document.createElement('td')
        fw.innerHTML = signal.modem?.fw_ver
        entry.append(fw)

        let temp = document.createElement('td')
        temp.innerHTML = signal.modem?.temp
        entry.append(temp)

        let signal_strength = document.createElement('td')
        signal_strength.innerHTML = signal.modem?.dbm
        entry.append(signal_strength)

        let cpu = document.createElement('td')
        cpu.innerHTML = (signal.modem?.cpu*100).toFixed(2)
        entry.append(cpu)

        let view = document.createElement('td')
        let viewBtn = document.createElement('button')
        viewBtn.classList.add('btn','btn-primary')
        viewBtn.setAttribute('type','button')
        viewBtn.innerHTML='View'
        view.append(viewBtn)
        entry.append(view)
        viewBtn.addEventListener('click',drawModal)

        table_data.append(entry)
    })
}

function update(){
    let handler = new EventSource(`http://${ip}/modem_listen`)

    handler.addEventListener('modem', (e) => {
        const data_obj = JSON.parse(e.data)
        let signal = JSON.parse(sessionStorage.getItem(data_obj.ip))
        if (!signal){
            signal = {}
        }
        signal.modem=data_obj.modem
        sessionStorage.setItem(data_obj.ip,JSON.stringify(signal))
    })


    handler.addEventListener("timestamp", (e)=>{
        const com_obj = JSON.parse(e.data)
        let local_com = JSON.parse(sessionStorage.getItem(com_obj.ip))
        local_com.time = com_obj.time
        sessionStorage.setItem(com_obj.ip,JSON.stringify(local_com))
    })

    handler.addEventListener('error',(e)=>{
        console.log(e)
        e.target.close()
        close_listen()
        // window.alert('Unable to connect to backend. Closing Listener...')
    })
        
        //todo: handle no response| update: partially handled
    async function close_listen (){
        let res = fetch(`http://${ip}/pause_modem_listen`,{
            method: 'POST',
            data: {pause:true}
        })
        console.log('tried to closes')
        handler.close()
    }
    addEventListener('beforeunload',close_listen)
}

function dblToChange(e){
    let elem = e
    let info = elem.innerHTML
    let input = document.createElement('input')
    input.value=info
    input.setAttribute('type','text')
    input.classList.add('form-control-sm')
    input.style.width='100px'
    elem.replaceWith(input)
    if (elem.id.includes('loc_port')){
        
        input.addEventListener('input',(e)=>{
            let ind = e.target.id.split('-')[1]
            let low = parseInt(document.getElementById(`int_port_start-${ind}`).value)
            let up = parseInt(document.getElementById(`int_port_end-${ind}`).value)
            e.target.nextElementSibling.innerHTML=parseInt(input.value)+up-low
        })
    }
    if (elem.id.includes('int_port')){
        input.addEventListener('input',(e)=>{
            let val
            if (e.target.nextElementSibling){
                val = parseInt(e.target.nextElementSibling.value)-parseInt(e.target.value)
            } else {
                val = parseInt(e.target.value)-parseInt(e.target.previousElementSibling.value)
            }
            let ind = e.target.id.split('-')[1]
            let tempElem = document.getElementById(`link+${ind}`)
            tempElem.innerHTML = parseInt(document.getElementById(`loc_port-${ind}`).value)+val
        })
    }
    input.id=elem.id
}

function recInpSearch(elem,changes){
    
    for (let child of elem.children){
        if (child.tagName?.toLocaleLowerCase()=='input'){
            let id 
            if (child.id.includes('-')){
                id = child.id.split('-')[0]
            }else{
                id = child.id.split('+')[0]
            }
            changes[id]=child.value
        }
        else {
            if (child.children.length>0){
                recInpSearch(child,changes)
            }
        }
    }
}

async function updateEntry(e){
    let cog_id = document.getElementById('cog-id-conf').innerHTML
    let data = JSON.parse(sessionStorage.getItem(cog_id))
    let changes = Array()
    let modal = e.target.parentElement
    recInpSearch(modal,changes)
    console.log(changes)

    let formData = new FormData()
    for (let change of changes){
        data[change.id.slice(0,-4)] = change.value
        formData.append(change.id.slice(0,-4),change.value)
    }
    formData.append('cog_id',cog_id)
    res = await fetch(`http://${ip}/update_from_input`,{
        method: 'POST',
        body: formData,
    })
    sessionStorage.setItem(cog_id,JSON.stringify(data))
    modal.close()
    let filters = getFilter()
    drawTable(filters)
}

function recChngInp(elem){
    if (elem.children.length<1){
        if (elem.id.includes(`-${ind}`)){
            dblToChange(elem)
        }
    }else{
        for (let child of elem.children){
            recChngInp(child)
        }
    }
}

async function editPfEntry(e){

    let btn = document.getElementById('sv-btn')
    btn.disabled=false
    ind = e.target.getAttribute('data-ind')
    e.target.disabled=true
    e.target.style.display='none'
    let delBtn = document.getElementById(`del-btn+${ind}`)
    delBtn.style.display='block'
    let entry  = e.target.parentElement.parentElement
    
    recChngInp(entry)
}
async function delPfEntry(e){

    ind = e.target.getAttribute('data-ind')
    let modal = document.getElementById('conf')
    let row = document.getElementById(modal.getAttribute('data-ip'))
    url = `http://${ip}/del_pf_table?ind=${ind}&ip=${modal.getAttribute('data-ip')}`
    res = await fetch(
        url,
        {
            method:'DELETE',
        }
    )
    drawModal({target:row.children[11].children[0]})
}

async function addPort(entry,modal){
    let changes = {}
    recInpSearch(entry,changes)
    changes.ip = modal.getAttribute('data-ip')
    url = `http://${ip}/add_pf_table`
    console.log(changes)
    res = await fetch(
        url,
        {
            method:'POST',
            body:JSON.stringify(changes),
            headers:{'Content-Type': 'application/json'}
        }
    )

}

async function savePortChanges(e){
    let table = document.getElementById('pf-table-body')
    let modal = e.target.parentElement
    let row = document.getElementById(modal.getAttribute('data-ip'))
    
    for (entry of table.children){
        let changes={}
        if (entry.getAttribute('data-new')){
            addPort(entry,modal)
            continue
        }
        recInpSearch(entry,changes)
        if (Object.keys(changes).length ===0){
            continue
        }
        let ind = entry.getAttribute('data-ind')
        changes.ind=ind
        changes.ip=modal.getAttribute('data-ip')
        url = `http://${ip}/edit_pf_table`

        res = await fetch(
            url,
            {
                method:'PUT',
                body:JSON.stringify(changes),
                headers:{'Content-Type': 'application/json'}
            }
        )
    }
    drawModal({target:row.children[11].children[0]})
}

async function drawModal(e){
    if(!confDial.open){
        confDial.showModal()

    }
    let entry = e.target.parentElement.parentElement.children[1]
    let ip_loc = entry.innerHTML
    confDial.setAttribute('data-ip',ip_loc)
    data = JSON.parse(sessionStorage.getItem(String(ip_loc)))


    let info = document.getElementById('main-info')
    let clients = document.getElementById('clients')
    let licenses = document.getElementById('licenses')
    let table = document.getElementById('pf-table-body')
    let saveButton = document.getElementById('sv-btn')
    

    saveButton.disabled=true
    
    info.innerHTML = ''
    clients.innerHTML = ''
    licenses.innerHTML = ''
    table.innerHTML = ''

    
    infoObj = {
        MAC:data?.modem?.mac,
        Latitude:data?.modem?.lat,
        Longitude:data?.modem?.lon,
        lastUpdate:data?.updated_at
    }

    for (let field in infoObj){
        let tempElem = document.createElement('div')
        let tempElemLabel = document.createElement('span')
        let tempElemValue = document.createElement('span')

        tempElem.append(tempElemLabel)
        tempElem.append(tempElemValue)
        info.append(tempElem)

        tempElemLabel.innerHTML=field+'  :'
        tempElemValue.innerHTML='  '+infoObj[field]
    }

    for (let client of data?.modem?.clients){
        let tempElem = document.createElement('div')
        let tempElemLabel = document.createElement('span')
        let tempElemValue = document.createElement('span')

        tempElem.append(tempElemLabel)
        tempElem.append(tempElemValue)
        clients.append(tempElem)

        tempElemLabel.innerHTML=client?.ip_address+'  :'
        tempElemValue.innerHTML='  '+ client?.mac
    }

    console.log(data?.modem?.licenses)
    if (data?.modem?.licenses.length!=0){
        for (let license of data?.modem?.licenses){
            let tempElem = document.createElement('div')
            let tempElemName = document.createElement('span')
            let tempElemId = document.createElement('span')
            let tempElemExp = document.createElement('span')
            tempElem.style.display = 'flex'
            tempElemName.style.width = '250px'
            tempElemId.style.width = '400px'
            tempElemExp.style.width = '200px'
            tempElemId.style.borderLeft = 'solid'
            tempElemName.style.borderLeft = 'solid'
            tempElemExp.style.borderLeft = 'solid'

    
            tempElem.append(tempElemName)
            tempElem.append(tempElemId)
            tempElem.append(tempElemExp)
            licenses.append(tempElem)
    
            tempElemName.innerHTML=license[1]
            tempElemId.innerHTML=license[0]
            tempElemExp.innerHTML=`Expires in ${license[3]} days`
        }

    } else {
        licenses.innerHTML='No Licenses'
    }
    let url = `http://${ip}/get_pf_table?`+new URLSearchParams({
        ip:ip_loc
    })
    let pf = await fetch(url,
        {
            method:'GET',        
            headers: {
                Accept: "application/json",
            },
        }
    )
    let ports = await pf.json()
    let port_ind = 0
    for (let entry of ports){
        let sTblDR = document.createElement('tr')
        let sTblD0 = document.createElement('td')
        let sTblD1 = document.createElement('td')
        let sTblD2 = document.createElement('td')
        let sTblD3 = document.createElement('td')
        let sTblD4 = document.createElement('td')
        let sTblD5 = document.createElement('td')
        let editBtn = document.createElement('button')
        let delBtn = document.createElement('button')
        let ip_locElem = document.createElement('span')
        let wanS = document.createElement('span')
        let wanE = document.createElement('span')
        let lan = document.createElement('span')
        let enab = document.createElement('span')
        let proto = document.createElement('span')
        let name = document.createElement('span')
        let linkedPort = document.createElement('span')


        ip_locElem.innerHTML=entry.ip_address
        wanS.innerHTML = entry.wan_port_start
        wanE.innerHTML = entry.wan_port_end
        lan.innerHTML = entry.lan_port_offt
        enab.innerHTML = entry.enabled
        proto.innerHTML = entry.protocol
        name.innerHTML = entry.name
        linkedPort.innerHTML = entry.lan_port_offt+entry.wan_port_end-entry.wan_port_start

        ip_locElem.id=`ip_loc-${port_ind}`
        wanS.id = `int_port_start-${port_ind}`
        wanE.id = `int_port_end-${port_ind}`
        lan.id = `loc_port-${port_ind}`
        enab.id = `enable-${port_ind}`
        proto.id = `protocol-${port_ind}`
        name.id = `name-${port_ind}`
        linkedPort.id = `link+${port_ind}`

        editBtn.classList.add('btn','btn-success')
        delBtn.classList.add('btn','btn-danger')
        delBtn.id = `del-btn+${port_ind}`

        editBtn.setAttribute('data-ind',port_ind)
        delBtn.setAttribute('data-ind',port_ind)
        sTblDR.setAttribute('data-ind',port_ind)

        delBtn.style.display='none'        
        editBtn.addEventListener('click',editPfEntry)
        delBtn.addEventListener('click',delPfEntry)

        sTblD1.append(name)
        sTblD2.append(wanS)
        sTblD2.append('-')
        sTblD2.append(wanE)
        sTblD3.append(ip_locElem)
        sTblD3.append(':')
        sTblD3.append(lan)
        sTblD3.append('-')
        sTblD3.append(linkedPort)
        sTblD4.append(proto)
        sTblD5.append(enab)
        editBtn.innerHTML='Edit'
        delBtn.innerHTML='Del'

        table.append(sTblDR)
        sTblDR.append(sTblD0)
        sTblDR.append(sTblD1)
        sTblDR.append(sTblD2)
        sTblDR.append(sTblD3)
        sTblDR.append(sTblD4)
        sTblDR.append(sTblD5)
        sTblD0.append(editBtn)
        sTblD0.append(delBtn)

        
        port_ind++
    }
}

addEventListener("load",async (event) =>  {

    const data = await get_data()
    d_json = await data.json()
    d_json.forEach(signal => {
        sessionStorage.setItem(signal.ip,JSON.stringify(signal))

    });
    let filters = getFilter()
    drawTable(filters)
})

addEventListener('load',update)

addButton.addEventListener('click',(e)=>{

    let table = document.getElementById('pf-table-body')
    let ind = parseInt(table.lastChild.getAttribute('data-ind'))+1
    let sTblDR = document.createElement('tr')
    sTblDR.setAttribute('data-new','true')
    saveButton.disabled=false

    let lan_input = (e)=>{
        let ind = e.target.id.split('-')[1]
        let input = document.getElementById(`loc_port-${ind}`)
        let low = parseInt(document.getElementById(`int_port_start-${ind}`).value)
        let up = parseInt(document.getElementById(`int_port_end-${ind}`).value)
        e.target.nextElementSibling.innerHTML=parseInt(input.value)+up-low
    }

    let wan_input = (e)=>{
        let val
        if (e.target.nextElementSibling){
            val = parseInt(e.target.nextElementSibling.value)-parseInt(e.target.value)
        } else {
            val = parseInt(e.target.value)-parseInt(e.target.previousElementSibling.value)
        }
        let ind = e.target.id.split('-')[1]
        let tempElem = document.getElementById(`link+${ind}`)
        tempElem.innerHTML = parseInt(document.getElementById(`loc_port-${ind}`).value)+val
    }
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
    guide.forEach((column)=>{
        let td = document.createElement('td')
        let i =0
        for (elem of column.elements){
            if (!elem.includes('span') && !elem.includes('input')){
                td.append(elem)
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
        sTblDR.append(td)
    })

    table.append(sTblDR)


})

saveButton.addEventListener('click',savePortChanges)

confDial.addEventListener("click", e => {
    
    const dialogDimensions = confDial.getBoundingClientRect()
    if (
      e.clientX < dialogDimensions.left ||
      e.clientX > dialogDimensions.right ||
      e.clientY < dialogDimensions.top ||
      e.clientY > dialogDimensions.bottom
    ) {
        confDial.close()
    }
  })

export_btn.addEventListener('click',async e=>{
    console.log(e)
    const myInit = {
        method: "GET",
        mode: "cors",
        cache: "default",
    };
    let data = await fetch(`http://${ip}/get_xlsx`,myInit)
    // let test = await data.formData()
    let a = document.createElement('a')
    let data_b = await data.blob()
    let url = URL.createObjectURL(data_b)
    a.href = url
    a.download = 'Radar.xlsx'
    document.body.appendChild(a)
    a.click()
    setTimeout(()=>{
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }, 0);
})

import_btn.addEventListener('click',async e=>{
    console.log(e)
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
            let res = await fetch(`http://${ip}/post_xlsx`,myInit)
            console.log(res)
            location.reload()
        }

    })
    file.click()



})

Array.from(filters.children).forEach( (filter)=>{
    filter.firstElementChild.addEventListener('click',filterState)
})

searchBox.addEventListener('input',() => {
    let filters = getFilter()
    drawTable(filters)
})

columnHeaders.addEventListener('click',(e) => {
    console.log(e)
    // make sure th was clicked
    let outStr
    let sortOrder = JSON.parse(sessionStorage.getItem('sortOrder'))

    if (e.target.classList.contains('sort-up')){
        outStr = e.target.innerHTML.slice(0,-1)+'&#8595'
        e.target.classList.remove('sort-up')
        e.target.classList.add('sort-down')
        

    } else {
        if (e.target.classList.contains('no-sort')){
            outStr = e.target.innerHTML.slice(0,-1)+'&#8593'
            e.target.classList.remove('no-sort')
            e.target.classList.add('sort-up')
            sortOrder.push(e.target.id)
        }
        if (e.target.classList.contains('sort-down')){
            outStr = e.target.innerHTML.slice(0,-1)+' '
            e.target.classList.remove('sort-down')
            e.target.classList.add('no-sort')
            let ind = sortOrder.findIndex((el)=>{return el==e.target.id})
            sortOrder.splice(ind,1)
        }

    }
    sessionStorage.setItem('sortOrder',JSON.stringify(sortOrder))
    e.target.innerHTML = outStr
    let filters = getFilter()
    drawTable(filters)
})




filterList.addEventListener('click',() => {
    let filters = getFilter()
    drawTable(filters)
})

setInterval(() => {
    let filters = getFilter()
    drawTable(filters)
},10000)