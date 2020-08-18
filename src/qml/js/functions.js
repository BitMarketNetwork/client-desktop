.pragma library

function loadImage(name) {
    if( !name || undefined === name){
        //console.exception("Empty image path:" + name)
        return "";
    }

    return Qt.resolvedUrl("../media/" + name)
}

function fontDescription(font){
    return `${font.pointSize};${font.family}`
}

function fontData(font){
    return {
        family: font.family,
        pointSize: Math.min(font.pointSize,30), // prevent against unreadable font
        bold: font.bold,
    }
}

function urlToPath(url){
    var path = url.toString();
    if (path.startsWith("file:///")) {
        path = path.substring(path.charAt(9) === ':' ? 8 : 7)
    }
    return  decodeURIComponent(path);
}

function explore(obj, pref = ''){
    if( obj instanceof Array ){
        var i;
        console.log(`${pref}=> array[${obj.length}]`)
        for(i=0;i<obj.length;++i){
            explore(obj[i] , pref + ":" + i);
        }
    }
    else if( obj instanceof Object ){
        console.log(`${pref}=> object`)
        for (var k in obj){
            if(obj[k] instanceof Function){
                
            }else{
                explore(obj[k], pref + ":" + k);
            }
        }
    }else{
        console.log(`${pref}:${obj} [${typeof obj}]`)
    }
}
