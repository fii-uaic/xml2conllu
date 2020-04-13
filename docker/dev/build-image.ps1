param(
    [parameter(Mandatory=$true)]
    [string]$Password
)

docker build -t xml2conllu:dev --build-arg password=$Password .
