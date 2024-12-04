pragma solidity ^0.8.0;

contract Verification {
    uint256 constant P   = 1208925819614629174706189;
    uint256 constant g1   = 71268528852831316311076975079190540529007687924137045429198239221085821340320;
    uint256 constant g2   = 107444586961954676114358403768738618907097969765753511016337400927285324288018;

    struct CommitData {
        uint256[] commit1;
        uint256[] commit2;
    }
    uint256 public c_sum1;
    uint256 public c_sum2;

    CommitData private commitData;

    // upload the sum of aggregated to smart contract
    function SumCtoSC(uint256 _s1, uint256 _s2) public {
        c_sum1 = _s1;
        c_sum2 = _s2;
    }

    // upload the commitment to smart contract
    function CommittoSC(uint256[2] memory _commit) public {
        commitData.commit1.push(_commit[0]);
        commitData.commit2.push(_commit[1]);
    }

    function getCommitData() public view returns (uint256[] memory, uint256[] memory) {
        return (commitData.commit1, commitData.commit2);
    }

    function verifyCommitment() public returns (bool) {
        uint256 commit1_mulmod = 1;
        uint256 commit2_mulmod = 1;

        for (uint256 i = 0; i < commitData.commit1.length; i++) {
            commit1_mulmod = mulmod(commit1_mulmod, uint256(commitData.commit1[i]), P);
        }
        for (uint256 i = 0; i < commitData.commit2.length; i++) {
            commit2_mulmod = mulmod(commit2_mulmod, uint256(commitData.commit2[i]), P);
        }

        if (commit1_mulmod == c_sum1 && commit2_mulmod == c_sum2) {
            return true;
        } else {
            return false;
        }
    }

}