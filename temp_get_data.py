organ_detail=""
def get_organ_detail():
    organ=input("Organ")
    blood_group=input("Blood group")
    result={
        "Organ":organ,
        "Blood_group":blood_group,
        "Organ_details_hash":str(organ_hash),
        "Organ_details_signed":SHA256.new(str(organ_hash).encode()).hexdigest(),
        "Doctor_cert_hash":SHA256.new(str(organ).encode()).hexdigest()
          }
    #with open("f{uid}_organ.json","w") as file:
    #    json.dump(result, file)
    organ_detail=result
