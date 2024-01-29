function check_header(request)
    local header = request:headers("Content-Type")

    if header == "" then
        request:headers("Content-Type", "application/json")
    end
end