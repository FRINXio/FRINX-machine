function swagger_auth_modal(r,jwt,scope,client_id)
    local body = r:body()
    if jwt == "true" then
        -- change token request to id_token
        body = body:gsub("response_type=token", "response_type=id_token");
        -- -- -- disable client_id input box and use default
        body = body:gsub("||A===x", "");
        body = body:gsub('client_id="%+encodeURIComponent%(p%)', 'client_id=' .. client_id .. '"');
        -- -- -- -- disable scopes selection and use default, add nonce query parameter
        body = body:gsub('O=o.get%("allowedScopes"%)||o.get%("scopes"%),', "");
        body = body:gsub('T%(%)%(c%)%?m%=c:F.a.List.isList%(c%)&&%(m=c.toArray%(%)%),m.length%>0', "true");
        body = body:gsub('scope="%+encodeURIComponent%(m.join%(v%)%)', 'scope=' .. scope .. '&nonce=678910"');
        r:headers('Content-Length', tostring(body:len()))
    end
    return body
end