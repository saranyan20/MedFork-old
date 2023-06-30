def new_transaction(self, kyc_hash, organ_hash, organ_hospital_signed_hash, organ_user_signed_hash,
                    hospital_id, digital_doctor_cert, user ):
    self.current_transactions.append({
        'kyc_hash': kyc_hash,
        'organ_hash': organ_hash,
        'organ_hospital_signed_hash': organ_hospital_signed_hash,
        'organ_user_signed_hash':organ_user_signed_hash,
        'hospital_id':hospital_id,
        'digital_doctor_cert':digital_doctor_cert,
        'user':user,
    })

    return self.last_block['index'] + 1
