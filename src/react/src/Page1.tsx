import { Link } from 'react-router-dom';
import Container from 'react-bootstrap/Container';
import ButtonLink from './ButtonLink';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

function Page1() {
  return (
    <Container>
      <h1>Page 1</h1>
      <div>
      <FontAwesomeIcon icon="coffee" />
      <FontAwesomeIcon icon={['fas', 'coffee']} />
      <FontAwesomeIcon icon={['far', 'coffee']} />
      {/* <FontAwesomeIcon icon={faCoffee} /> */}
        Your <FontAwesomeIcon icon="coffee" /> is hot and ready!
      </div>
      <Link to="/systems" component={ButtonLink}>
        Go to Systems
      </Link>
    </Container>
  );
}

export default Page1;
