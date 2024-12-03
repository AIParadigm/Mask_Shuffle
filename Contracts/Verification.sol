pragma solidity ^0.8.0;

contract Verification {

    function modPow(uint256 base, uint256 exponent, uint256 modulus) internal returns (uint256) {
	    uint256[6] memory input = [32,32,32,base,exponent,modulus];
	    uint256[1] memory result;
	    assembly {
	      if iszero(call(not(0), 0x05, 0, input, 0xc0, result, 0x20)) {
	        revert(0, 0)
	      }
	    }
	    return result[0];
	}

    uint256 constant P   = 1208925819614629174706189;
    uint256 constant g1   = 71268528852831316311076975079190540529007687924137045429198239221085821340320;
    uint256 constant g2   = 107444586961954676114358403768738618907097969765753511016337400927285324288018;

    struct GradData {
        uint256[] grad;
    }

    struct CommitData {
        uint256[] commit1;
        uint256[] commit2;
    }
    uint256 public sum1;
    uint256 public sum2;

    GradData private gradData;
    CommitData private commitData;
    function GradtoSC(uint256[] memory _grad) public {
        gradData = GradData({
            grad: _grad
        });
        (sum1, sum2) = calculateGradSum(_grad);
    }

    // upload the sum of aggregated to smart contract
    function SumtoSC(uint256 _s1, uint256 _s2) public {
        sum1 = _s1;
        sum2 = _s2;
    }

    // upload the commitment to smart contract
    function CommittoSC(uint256[2] memory _commit) public {
        commitData.commit1.push(_commit[0]);
        commitData.commit2.push(_commit[1]);
    }

    function getGradData() public view returns (uint256[] memory) {
        return gradData.grad;
    }

    function getCommitData() public view returns (uint256[] memory, uint256[] memory) {
        return (commitData.commit1, commitData.commit2);
    }

    function calculateGradSum(uint256[] memory grad) public pure returns (uint256, uint256) {
        uint256 halfLength = grad.length / 2;
        uint256 s1 = 0;
        uint256 s2 = 0;

        for (uint256 i = 0; i < halfLength; i++) {
            s1 = (s1 + grad[i]);
        }
        for (uint256 i = halfLength; i < grad.length; i++) {
            s2 = (s2 + grad[i]);
        }

        return (s1, s2);
    }
    // calculate the commit of the sum of aggregated grad
    function calculateCommitment() public returns (uint256, uint256) {

        uint256 result1 = modPow(g1, sum1, P);
        uint256 result2 = modPow(g2, sum2, P);

        return (result1, result2);
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

        (uint256 c_s1, uint256 c_s2) = calculateCommitment();
        if (commit1_mulmod == c_s1 && commit2_mulmod == c_s2) {
            return true;
        } else {
            return false;
        }
    }

}