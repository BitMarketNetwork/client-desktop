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
        for(i=0;i<obj.length;++i){
            explore(obj[i]);
        }
    }
    else if( obj instanceof Object ){
        for (var k in obj){
            if(obj[k] instanceof Function){
                continue
            }

            console.log(`${pref}:${k} => ${obj[k]}`)
        }
    }else{
        console.log(`${pref}:${obj}`)
    }
}
