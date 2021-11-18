local char_to_hex = function(c)
    return string.format("%%%02X", string.byte(c))
end

function urlencode(r)
    local url = r:url()
    path, query = url:match("([^,]+)?([^,]+)")
    url = url:gsub(";", char_to_hex)
    return url
end