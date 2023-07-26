let ip = location.host
sessionStorage.setItem('sortOrder',JSON.stringify(Array()))

const export_btn = document.getElementById('export_btn')
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
    const data = await fetch(`http://${ip}/get_radar_data`,myInit)
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
        type:['radar_ccus','0','name'],
        comm:['modem_online'],
        ip:['ip'],
        firm:['radar_ccus','0','version'],
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
    let count656 = 0
    let count650 = 0
    let count600 = 0
    let noneCount = 0
    const signals = new Array()
    let searchStr = document.getElementById('search').value

    for (let i = 0; i<sessionStorage.length;i++){
        let cog_id = sessionStorage.key(i)
        if (cog_id=='sortOrder'){
            continue
        }
        allSignalCount++
        let signal = JSON.parse(sessionStorage.getItem(cog_id))

        let filt1 = signal.radar_ccus?.some((d)=>d.name?.includes('656'))
        let filt2 = signal.radar_ccus?.some((d)=>d.name?.includes('650'))
        let filt3 = signal.radar_ccus?.some((d)=>d.name?.includes('600'))
        if (filt1){
            count656++
        }
        if (filt2){
            count650++
        }
        if (filt3){
            count600++
        }
        if (!(filt1||filt2||filt3)){
            noneCount++
        }
        signals.push(signal)
    }

    let aCountElem = document.getElementById("all-signal-count")
    let count656Elem = document.getElementById("656-count")
    let count650Elem = document.getElementById("650-count")
    let count600Elem = document.getElementById("600-count")
    let noCountElem = document.getElementById("no-count")

    aCountElem.innerHTML = `( ${allSignalCount} )`
    count656Elem.innerHTML = `( ${count656} )`
    count650Elem.innerHTML = `( ${count650} )`
    count600Elem.innerHTML = `( ${count600} )`
    noCountElem.innerHTML = `( ${noneCount} )`

    let filterdSignals
    if (filters.baseFilter =="656-filter"){
        filterdSignals = signals.filter((signal) => {
            let cond = signal.radar_ccus?.some((d)=>d.name?.includes('656'))
            cond = matchSearch(cond,searchStr,signal)
            return cond
        })
    }
    if (filters.baseFilter =="650-filter"){
        filterdSignals = signals.filter((signal) => {
            let cond = signal.radar_ccus?.some((d)=>d.name?.includes('650'))
            cond = matchSearch(cond,searchStr,signal)
            
            return cond
        })
        
    }
    if (filters.baseFilter =="600-filter"){
        filterdSignals = signals.filter((signal) => {
            let cond = signal.radar_ccus?.some((d)=>d.name?.includes('600'))

            cond = matchSearch(cond,searchStr,signal)
            return cond
        })
    } 
    if (filters.baseFilter =="no-filter"){
        filterdSignals = signals.filter((signal) => {
            let cond = signal.radar_ccus?.some((d)=>d.name?.includes('656'))
            cond = signal.radar_ccus?.some((d)=>d.name?.includes('650')) ||cond
            cond = signal.radar_ccus?.some((d)=>d.name?.includes('600')) || cond
            cond = !cond
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

        let type = document.createElement('td')
        type.innerHTML = signal.radar_ccus?.[0]?.name
        entry.append(type)
            
        let comm = document.createElement('td')
        comm.innerHTML = signal.modem_online
        entry.append(comm)

        let ip = document.createElement('td')
        ip.innerHTML = signal.ip
        entry.append(ip)

        let ver = document.createElement('td')
        ver.innerHTML = signal.radar_ccus?.[0]?.version
        entry.append(ver)

        let ts = document.createElement('td')
        ts.innerHTML = signal.updated_at ||'00:00:00'
        entry.append(ts)


        table_data.append(entry)
    })
}



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
    let filters = getFilter()
    drawTable(filters)
})


addEventListener('load',update)

function update(){
    let handler = new EventSource(`http://${ip}/radar_listen`)

    handler.addEventListener('radar', (e) => {
        const data_obj = JSON.parse(e.data)
        let signal = JSON.parse(sessionStorage.getItem(data_obj.cog_id))
        signal.devices=data_obj.devices
        sessionStorage.setItem(data_obj.cog_id,JSON.stringify(signal))
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
            close_listen()
            // window.alert('Unable to connect to backend. Closing Listener...')
        })
        
        //todo: handle no response| update: partially handled
        async function close_listen (){
            let res = fetch(`http://${ip}/pause_radar_listen`,{
                method: 'POST',
                data: {pause:true}
            })
            console.log('tried to closes')
            handler.close()
    }
    addEventListener('beforeunload',close_listen)
}
let filterList = document.getElementById('filter-list')
filterList.addEventListener('click',() => {
    let filters = getFilter()
    drawTable(filters)
})
setInterval(() => {
    let filters = getFilter()
    drawTable(filters)
},10000)

function dblToChange(e){
    let svBtn = document.getElementById('sv-btn')
    svBtn.disabled=false
    let elem = e.target
    let info = elem.innerHTML
    let input = document.createElement('input')
    input.value=info
    input.setAttribute('type','text')
    elem.replaceWith(input)
    input.id=elem.id
    elem.value = info
}

let confDial = document.getElementById('conf')
let data_table = document.getElementById('list')
data_table.addEventListener('click',(e)=>{
    confDial.showModal()
    if (e.target.tagName.toLocaleLowerCase()=='tr'){
        confDial.innerHTML = e.target.id
    } else {
        data = JSON.parse(sessionStorage.getItem(String(e.target.parentElement.id)))
        let info = document.getElementById('main-info')
        info.innerHTML = ''
        let cog_id = document.createElement('span')
        cog_id.id = 'cog-id-conf'
        let name = document.createElement('span')
        cog_id.innerHTML = data.cog_id
        cog_id.classList.add('border-end','pe-3','me-3')
        name.innerHTML = data.name
        name.id='name-inp'
        name.addEventListener('dblclick',dblToChange)
        info.append(cog_id)
        info.append(name)
        info.classList.add('border-bottom','pb-2')


        let ipConf = document.getElementById('ip-conf')
        ipConf.innerHTML = ''
        let ipLab = document.createElement('span')
        let ip = document.createElement('span')
        ip.id = 'ip-inp'
        ipLab.innerHTML = 'IP Address : '
        ip.innerHTML = data.ip
        ip.addEventListener('dblclick',dblToChange)
        ipConf.append(ipLab)
        ipConf.append(ip)

        metaInfo = document.getElementById('meta-info')
        let nMatrixTag = document.getElementById('n-matrix-tag')
        let nCCUTag = document.getElementById('n-advance-tag')
        let nAdvancedTag = document.getElementById('n-ccu-tag')
        nMatrixTag.innerHTML = "Number of Recorded Matrix: "
        nCCUTag.innerHTML = "Number of Recorded Advance: "
        nAdvancedTag.innerHTML="Number of Recorded CCU: "


        let nMatrix = document.createElement('span')
        nMatrix.addEventListener('dblclick',dblToChange)
        nMatrix.innerHTML = data.n_matrix
        nMatrix.id='n_matrix-inp'
        let nCCU = document.createElement('span')
        nCCU.addEventListener('dblclick',dblToChange)
        nCCU.innerHTML=data.n_ccu
        nCCU.id='n_ccu-inp'
        let nAdvanced = document.createElement('span')
        nAdvanced.addEventListener('dblclick',dblToChange)
        nAdvanced.innerHTML=data.n_advance
        nAdvanced.id='n_advance-inp'
        nMatrixTag.append(nMatrix)
        nCCUTag.append(nCCU)
        nAdvancedTag.append(nAdvanced)

        let cculabel = document.getElementById('ccu-title')
        let ccus = document.getElementById('ccus')
        ccus.innerHTML=''
        if (data.radar_ccus.length){
            ccus.style.display='block'
            cculabel.style.display='block'
            let i=0
            for(let ccu of data.radar_ccus){
                let ccu_acc = document.createElement('div')
                let acc_head = document.createElement('p')
                let accBtn = document.createElement('button')
                let drop = document.createElement('div')
                let dropBody = document.createElement('div')
                
                
                ccu_acc.classList.add('accordion-item')
                acc_head.classList.add('accordion-header')
                accBtn.classList.add('d-flex','accordion-button','collapsed')
                drop.classList.add('accordion-collapse','collapse')
                dropBody.classList.add('accordion-body')
                
                
                accBtn.setAttribute('data-bs-toggle','collapse')
                accBtn.setAttribute('data-bs-target',`#radar${i}`)
                accBtn.setAttribute('type','button')
                accBtn.setAttribute('aria-expanded',`${i}`)
                accBtn.setAttribute('aria-controls','button')
                drop.setAttribute('data-bs-parent','#ccus')
                drop.id = `radar${i}`
                
                
                ccu_acc.append(acc_head)
                ccus.append(ccu_acc)
                acc_head.append(accBtn)
                ccu_acc.append(drop)
                drop.append(dropBody)
                
                
                let elem = document.createElement('span')
                elem.innerHTML=ccu.name
                elem.style.width='100px'
                accBtn.append(elem)
                elem = document.createElement('span')
                elem.innerHTML=ccu.serial
                elem.style.width='200px'
                accBtn.append(elem)
                
                
                elem = document.createElement('p')
                elem.innerHTML=`MAC Address: ${ccu.mac}`
                dropBody.append(elem)
                elem = document.createElement('p')
                elem.innerHTML=`Version: ${ccu.version}`
                dropBody.append(elem)
                elem = document.createElement('p')
                elem.innerHTML=`Port: ${ccu.port}`
                dropBody.append(elem)
                i++
                let j=0
                let panelsLabel = document.createElement('h4')
                panelsLabel
                panelsLabel.innerHTML = 'Sensors'
                dropBody.append(panelsLabel)
                
                let sTbl = document.createElement('table')
                let sTblH = document.createElement('thead')
                let sTblR = document.createElement('tr')
                let sTblH1 = document.createElement('th')
                let sTblH2 = document.createElement('th')
                let sTblH3 = document.createElement('th')
                let sTblH4 = document.createElement('th')
                let sTblH5 = document.createElement('th')

                sTbl.classList.add('table')

                sTblH1.scope = "col"
                sTblH1.innerHTML = 'Name'
                sTblH2.scope = "col"
                sTblH2.innerHTML = 'S/N'
                sTblH3.scope = "col"
                sTblH3.innerHTML = 'Type'
                sTblH4.scope = "col"
                sTblH4.innerHTML = 'Channels'
                sTblH5.scope = "col"
                sTblH5.innerHTML = 'Port'

                dropBody.append(sTbl)
                sTbl.append(sTblH)
                sTblH.append(sTblR)
                sTblR.append(sTblH1)
                sTblR.append(sTblH2)
                sTblR.append(sTblH3)
                sTblR.append(sTblH4)
                sTblR.append(sTblH5)
                let sTblBdy = document.createElement('tbody')
                sTbl.append(sTblBdy)
                for (let panel of ccu.sensors){
                    let sTblDR = document.createElement('tr')
                    let sTblD1 = document.createElement('td')
                    let sTblD2 = document.createElement('td')
                    let sTblD3 = document.createElement('td')
                    let sTblD4 = document.createElement('td')
                    let sTblD5 = document.createElement('td')

                    sTblD1.innerHTML=panel.name
                    sTblD2.innerHTML=panel.serialNumber
                    sTblD3.innerHTML=panel.type
                    sTblD4.innerHTML=panel.channels.map(x =>+ x)
                    sTblD5.innerHTML=panel.port

                    sTblBdy.append(sTblDR)
                    sTblDR.append(sTblD1)
                    sTblDR.append(sTblD2)
                    sTblDR.append(sTblD3)
                    sTblDR.append(sTblD4)
                    sTblDR.append(sTblD5)
                }
                
            } 
        } else {
            ccus.style.display='none'
            cculabel.style.display='none'
        }

        let saveButton = document.getElementById('sv-btn')
        saveButton.disabled=true
    }
})

function recInpSearch(elem,changes){
    
    for (let child of elem.children){
        if (child.tagName?.toLocaleLowerCase()=='input'){
            let change = {
                id:child.id,
                value:child.value
            }
            changes.push(change)
        }
        else {
            if (child.children.length>0){
                recInpSearch(child,changes)
            }
        }
    }
}

let saveButton = document.getElementById('sv-btn')
saveButton.addEventListener('click',updateEntry)
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
