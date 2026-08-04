package omniguard

default allow = false

allow {
    input.role == "admin"
}

allow {
    input.role == "senior-dev"
    input.tool != "delete_database"
}

allow {
    input.role == "junior-dev"
    input.tool == "read_repo"
}