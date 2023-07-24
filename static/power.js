let ip = location.host

const export_btn = document.getElementById('export_btn')
export_btn.addEventListener('click',async e=>{
    console.log(e)
    const myInit = {
        method: "GET",
        mode: "cors",
        cache: "default",
    };
    let data = await fetch('http://127.0.0.1:5000/get_xlsx',myInit)
    // let test = await data.formData()
    let a = document.createElement('a')
    let data_b = await data.blob()
    let url = URL.createObjectURL(data_b)
    a.href = url
    a.download = 'Signals.xlsx'
    document.body.appendChild(a)
    a.click()
    setTimeout(()=>{
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }, 0);
})

const import_btn = document.getElementById('import_btn')
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

async function get_data(){
    const myInit = {
        method: "GET",
        headers: {
            Accept: "application/json",
        },
        mode: "cors",
        cache: "default",
    };
    const data = await fetch(`http://${ip}/get_data`,myInit)
    console.log(data)
    return data
}
addEventListener("load",async (event) =>  {

    const data = await get_data()
    d_json = await data.json()
    d_json.forEach(signal => {
        sessionStorage.setItem(signal.cog_id,JSON.stringify(signal))

    });
    let filters = getFilter()
    drawTable(filters)
})


function filterState(e){
    let filters = document.getElementById('filters')
    Array.from(filters.children).forEach( (filter)=>{
        filter.firstElementChild.classList.remove('active')
    })
    e.target.classList.add("active")
}

let filters = document.getElementById('filters')
Array.from(filters.children).forEach( (filter)=>{
    filter.firstElementChild.addEventListener('click',filterState)
})

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
        signal.name.toLocaleLowerCase('en-US').includes(searchStr.toLocaleLowerCase('en-US')) 
        || String(signal.cog_id).includes(searchStr) 
        || signal.ip.includes(searchStr) 
        || String(signal.meters[0]?.esi_id).includes(searchStr)
    )
    return cond
}

let searchBox = document.getElementById('search')
searchBox.addEventListener('input',() => {
    let filters = getFilter()
    drawTable(filters)
})
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
        name:['name'],
        status:['meters','0','online_status'],
        comm:['modem_online'],
        ip:['ip'],
        esi_id:['esi_id'],
        time:['updated_at'],
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
    let PowerOutageCount = 0
    let ComOutageCount = 0
    let PowerCommCount = 0
    const signals = new Array()
    let searchStr = document.getElementById('search').value

    for (let i = 0; i<sessionStorage.length;i++){
        let cog_id = sessionStorage.key(i)
        if (cog_id=='sortOrder'){
            continue
        }
        allSignalCount++
        let signal = JSON.parse(sessionStorage.getItem(cog_id))
        let filt1 = signal.modem_online !== true
        let filt2 = signal.meters[0]?.online_status != "ON"
        if (filt1){
            ComOutageCount = ComOutageCount+1
        }
        if (filt2){
            PowerOutageCount = PowerOutageCount+1
        }
        if (filt1&&filt2){
            PowerCommCount = PowerCommCount +1
        }
        signals.push(signal)
    }

    let aCountElem = document.getElementById("all-signal-count")
    let pCountElem = document.getElementById("power-out-count")
    let cCountElem = document.getElementById("com-out-count")
    let pcCountElem = document.getElementById("power-com-count")

    aCountElem.innerHTML = `( ${allSignalCount} )`
    pCountElem.innerHTML = `( ${PowerOutageCount} )`
    cCountElem.innerHTML = `( ${ComOutageCount} )`
    pcCountElem.innerHTML = `( ${PowerCommCount} )`
    let filterdSignals
    if (filters.baseFilter =="power-out-filter"){
        filterdSignals = signals.filter((signal) => {
            let cond = signal.meters[0]?.online_status!="ON"
            cond = matchSearch(cond,searchStr,signal)
            return cond
        })
    }
    if (filters.baseFilter =="com-out-filter"){
        filterdSignals = signals.filter((signal) => {
            let cond = signal.modem_online !== true
            cond = matchSearch(cond,searchStr,signal)
            
            return cond
        })
        
    }
    if (filters.baseFilter =="power-com-out-filter"){
        filterdSignals = signals.filter((signal) => {
            let cond = signal.meters[0]?.online_status!="ON" && signal.modem_online !== true

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
    filterdSignals.sort(getSortFunction())
    const table_data = document.getElementById('list')
    table_data.innerHTML = ""    
    filterdSignals.forEach((signal)=>{
        let entry = document.createElement('tr')
        entry.id = signal.cog_id

        let id = document.createElement('th')
        id.setAttribute('scope','row')
        id.innerHTML = signal.cog_id
        entry.append(id)

        let entry_name = document.createElement('td')
        entry_name.innerHTML = signal.name
        entry.append(entry_name)

        let status = document.createElement('td')
        if (signal.meters[0]){
            status.innerHTML = signal.meters[0].online_status || '&#9203'
        } else {
            status.innerHTML = 'no_meter'
        }
        status.setAttribute('title','Not Updated')
        entry.append(status)
            
        let comm = document.createElement('td')
        comm.innerHTML = signal.modem_online || '&#9203'
        entry.append(comm)

        let ip = document.createElement('td')
        ip.innerHTML = signal.ip
        entry.append(ip)


        let esi = document.createElement('td')
        if (signal.meters[0]){
            esi.innerHTML = signal.meters[0].esi_id

        } else {
            esi.innerHTML = 'N/A'
        }
        entry.append(esi)

        let ts = document.createElement('td')
        ts.innerHTML = signal.updated_at ||'00:00:00'
        entry.append(ts)


        table_data.append(entry)
    })
}
sessionStorage.setItem('sortOrder',JSON.stringify(Array()))
columnHeaders = document.getElementById('headers')
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
})

addEventListener('load',update)
function update(){
    let handler = new EventSource(`http://${ip}/listen`)

    handler.addEventListener('oncor', (e) => {
        const meter_string = e.data
        const meter_obj = JSON.parse(e.data)
        let local_meter = JSON.parse(sessionStorage.getItem(meter_obj.cog_id))
        if (!local_meter.meters[0]){
            local_meter.meters[0] = {}
        }
        local_meter.meters[0].online_status = meter_obj.online_status
        local_meter.meters[0].esi_id = meter_obj.esi_id
        sessionStorage.setItem(meter_obj.cog_id,JSON.stringify(local_meter))
    })
    

    
    handler.addEventListener("ping_comm", (e)=>{
        const com_obj = JSON.parse(e.data)
        let local_com = JSON.parse(sessionStorage.getItem(com_obj.cog_id))
        local_com.modem_online = com_obj.modem_online
        sessionStorage.setItem(com_obj.cog_id,JSON.stringify(local_com))
    })

        handler.addEventListener("timestamp", (e)=>{
            const com_obj = JSON.parse(e.data)
            let local_com = JSON.parse(sessionStorage.getItem(com_obj.cog_id))
            local_com.time = com_obj.time
            sessionStorage.setItem(com_obj.cog_id,JSON.stringify(local_com))

        })

        handler.addEventListener('error',(e)=>{
            console.log(e)
            e.target.close()
            window.alert('Unable to connect to backend. Closing Listener...')
        })
        
        //todo: handle no response| update: partially handled
        async function close_listen (){
            let res = fetch(`http://${ip}/pause_listen`,{
                method: 'POST',
                data: {pause:true}
            })
            console.log('tried to closes')
            handler.close()
    }
    addEventListener('beforeunload',close_listen)
}

window.addEventListener('click',() => {
    let filters = getFilter()
    drawTable(filters)
})
setInterval(() => {
    let filters = getFilter()
    drawTable(filters)
},10000)